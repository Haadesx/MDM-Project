"""Forecast adapters and frozen supervised models for the experiment."""

import warnings

import numpy as np


def _counts(counts):
    values = np.asarray(counts, dtype=np.float32)
    if values.ndim != 2 or values.shape[1] != 90 or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('counts must be finite nonnegative B x 90')
    return values


def _results(raw, statuses, errors):
    raw = np.asarray(raw, dtype=float)
    forecasts = raw.copy()
    clipped = []
    minima = []
    for i, row in enumerate(raw):
        if statuses[i] != 'failed' and not np.isfinite(row).all():
            statuses[i], errors[i] = 'failed', 'nonfinite forecast'
            forecasts[i] = np.nan
            raw[i] = np.nan
        clipped.append(int((row < 0).sum()) if statuses[i] != 'failed' else 0)
        minima.append(float(np.min(row)) if statuses[i] != 'failed' else None)
    forecasts = np.maximum(forecasts, 0)
    return {'raw': raw, 'forecast': forecasts, 'status': statuses, 'error': errors,
            'n_values_clipped': clipped, 'min_raw': minima}


def _forecast_arima(series, diagnostic):
    from statsmodels.tsa.arima.model import ARIMA

    model = ARIMA(series, order=(1, 0, 0), trend='c', seasonal_order=(0, 0, 0, 0),
                  enforce_stationarity=True, enforce_invertibility=True)
    attempts = diagnostic['optimizer_attempts'] = []
    for solver, options in (('default', {}), ('bfgs', {'method': 'bfgs', 'maxiter': 150})):
        with warnings.catch_warnings(record=True) as caught:
            fitted = model.fit(method='statespace', method_kwargs=options)
        messages = [str(w.message) for w in caught]
        stats = {key: value.item() if isinstance(value, np.generic) else value
                 for key, value in fitted.mle_retvals.items()
                 if isinstance(value, (int, float, np.integer, np.floating, np.bool_)) and np.isfinite(value)}
        converged = bool(stats.get('converged')) and not any('converg' in text.lower() for text in messages)
        attempts.append({**stats, 'solver': solver, 'converged': converged, 'warnings': messages})
        if converged:
            return fitted.forecast(steps=30)
    raise RuntimeError('ARIMA state-space optimizers did not converge')


def forecast_classical(model_id, counts, origin, backend=None, seed=20261120):
    import pandas as pd
    values = _counts(counts)
    if model_id not in ('arima', 'prophet'):
        raise ValueError('unknown classical model')
    end = pd.Timestamp(origin).tz_localize(None).normalize()
    rows, statuses, errors, warning_rows, diagnostics = [], [], [], [], []
    for series in values:
        if np.all(series == series[0]):
            rows.append(np.full(30, series[0])); statuses.append('constant_series'); errors.append(None)
            warning_rows.append([]); diagnostics.append({})
            continue
        caught, diagnostic = [], {}
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                if backend is not None:
                    predicted = backend(series)
                elif model_id == 'arima':
                    predicted = _forecast_arima(series, diagnostic)
                else:
                    from prophet import Prophet
                    model = Prophet(growth='linear', weekly_seasonality=False, yearly_seasonality=False, daily_seasonality=False, n_changepoints=5, changepoint_prior_scale=0.05, seasonality_mode='additive', uncertainty_samples=0)
                    model.fit(pd.DataFrame({'ds': pd.date_range(end=end, periods=90), 'y': series}), seed=seed)
                    diagnostic = {'seed': seed}
                    predicted = model.predict(pd.DataFrame({'ds': pd.date_range(start=end + pd.Timedelta(days=1), periods=30)}))['yhat']
                if any('converg' in str(w.message).lower() for w in caught):
                    raise RuntimeError('optimizer convergence warning')
            predicted = np.asarray(predicted, dtype=float)
            if predicted.shape != (30,):
                raise ValueError('forecast must have 30 values')
            rows.append(predicted); statuses.append('ok'); errors.append(None)
        except Exception as exc:
            rows.append(np.full(30, np.nan)); statuses.append('failed'); errors.append(str(exc))
        optimizer_warnings = [text for attempt in diagnostic.get('optimizer_attempts', [])
                              for text in attempt['warnings']]
        warning_rows.append(optimizer_warnings + [str(w.message) for w in caught])
        diagnostics.append(diagnostic)
    return _results(rows, statuses, errors) | {'warnings': warning_rows, 'diagnostics': diagnostics}


class TimestralAdapter:
    def __init__(self, forecaster):
        self.forecaster = forecaster

    def forecast(self, counts, covariates=None):
        values = _counts(counts)
        cov = None if covariates is None else np.asarray(covariates, dtype=np.float32)
        if cov is not None and (cov.shape != (len(values), 90, 2) or not np.isfinite(cov).all()):
            raise ValueError('covariates must be finite B x 90 x 2')
        try:
            result = self.forecaster.forecast(context=values[:, None, :], past_covariates=None if cov is None else cov.transpose(0, 2, 1), prediction_length=30, symmetric_averaging=True, clip_nonnegative=True)
            median = result.median
            if hasattr(median, 'detach'):
                median = median.detach().cpu().numpy()
            median = np.asarray(median)
            if median.shape != (len(values), 1, 30):
                raise ValueError('median must have shape B x 1 x 30')
            return _results(median[:, 0, :], ['ok'] * len(values), [None] * len(values))
        except Exception as exc:
            if 'out of memory' in str(exc).lower() and len(values) > 1:
                middle = len(values) // 2
                parts = [self.forecast(values[:middle], None if cov is None else cov[:middle]), self.forecast(values[middle:], None if cov is None else cov[middle:])]
                return {key: np.concatenate([part[key] for part in parts]) if key in ('raw', 'forecast') else sum((part[key] for part in parts), []) for key in parts[0]}
            return _results(np.full((len(values), 30), np.nan), ['failed'] * len(values), [str(exc)] * len(values))


def _pipeline(c):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return make_pipeline(StandardScaler(), LogisticRegression(C=c, solver='lbfgs', max_iter=2000, class_weight=None))


def _xy(x, y, width):
    x, y = np.asarray(x, dtype=float), np.asarray(y)
    if x.ndim != 2 or x.shape[1] != width or len(x) != len(y) or y.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('invalid features or labels')
    if not np.isin(y, [0, 1]).all() or len(np.unique(y)) != 2:
        raise ValueError('labels must contain both binary classes')
    return x, y


def _fit(model, x, y):
    from sklearn.exceptions import ConvergenceWarning
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        model.fit(x, y)
    return model


def fit_forecast_mapper(x, y):
    x, y = _xy(x, y, 30)
    if (x < 0).any():
        raise ValueError('forecasts must be nonnegative')
    return _fit(_pipeline(1), x, y)


def fit_topology_logistic(train_x, train_y, validation_x, validation_y, validation_origins):
    from sklearn.metrics import average_precision_score
    train_x, train_y = _xy(train_x, train_y, 5)
    validation_x = np.asarray(validation_x, dtype=float)
    validation_y = np.asarray(validation_y)
    origins = np.asarray(validation_origins)
    if validation_x.ndim != 2 or validation_x.shape[1] != 5 or not np.isfinite(validation_x).all() or len(validation_x) != len(validation_y) or len(origins) != len(validation_y) or not np.isin(validation_y, [0, 1]).all():
        raise ValueError('invalid validation data')
    scores = {}
    for c in (0.1, 1.0, 10.0):
        model = _fit(_pipeline(c), train_x, train_y)
        probabilities = model.predict_proba(validation_x)[:, 1]
        ap = [average_precision_score(validation_y[mask], probabilities[mask]) for origin in np.unique(origins) if (mask := origins == origin).any() and validation_y[mask].sum() > 0]
        if not ap:
            raise ValueError('no valid validation origins')
        scores[c] = float(np.mean(ap))
    selected = max(scores, key=scores.get)
    x, y = _xy(np.concatenate((train_x, validation_x)), np.concatenate((train_y, validation_y)), 5)
    return _fit(_pipeline(selected), x, y), selected, scores


TIMESTRAL_SOURCE_REVISION = 'a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff'
TIMESTRAL_WEIGHTS_REVISION = '9874d252ab0aae16f7f7c999f98f98d6ad7d8365'


def _source_revision():
    import importlib.metadata
    import json
    try:
        metadata = importlib.metadata.distribution('timestral').read_text('direct_url.json')
        source = json.loads(metadata) if metadata else {}
        if source.get('url', '').removesuffix('.git') != 'https://github.com/mistralai/timestral':
            return None
        return source.get('vcs_info', {}).get('commit_id')
    except importlib.metadata.PackageNotFoundError:
        return None


def load_timestral(device=None):
    import hashlib
    import importlib.metadata
    from pathlib import Path
    if _source_revision() != TIMESTRAL_SOURCE_REVISION:
        raise RuntimeError('Timestral official source revision is missing or differs from the pinned revision')
    import torch
    from huggingface_hub import hf_hub_download
    from timestral import TimestralForecaster
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    path = Path(hf_hub_download('mistralai/Timestral-209M', 'config.json', revision=TIMESTRAL_WEIGHTS_REVISION, local_files_only=True)).parent
    hf_hub_download('mistralai/Timestral-209M', 'model.safetensors', revision=TIMESTRAL_WEIGHTS_REVISION, local_files_only=True)
    hashes = {}
    for name in ('config.json', 'model.safetensors'):
        digest = hashlib.sha256()
        with (path / name).open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        hashes[name] = digest.hexdigest()
    forecaster = TimestralForecaster.from_pretrained(path, device=device)
    return TimestralAdapter(forecaster), {'source_revision': TIMESTRAL_SOURCE_REVISION, 'weights_revision': TIMESTRAL_WEIGHTS_REVISION, 'checkpoint': 'mistralai/Timestral-209M', 'device': str(device), 'dtype': str(next(forecaster.model.parameters()).dtype), 'timestral_version': importlib.metadata.version('timestral'), 'torch_version': torch.__version__, 'symmetric_averaging': True, 'clip_nonnegative': True, 'sha256': hashes}
