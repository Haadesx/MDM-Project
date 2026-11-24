import numpy as np
import pytest

from cooperalink.models import forecast_classical, TimestralAdapter, fit_forecast_mapper, fit_topology_logistic


def test_classical_constant_and_failure():
    result = forecast_classical('arima', np.array([[2.] * 90, list(range(90))]), '2023-01-01', backend=lambda x: (_ for _ in ()).throw(ValueError('failure')))
    assert result['status'] == ['constant_series', 'failed']
    assert np.array_equal(result['forecast'][0], np.full(30, 2.))
    assert np.isnan(result['forecast'][1]).all()
    assert 'failure' in result['error'][1]


def test_timestral_routes_and_clips():
    class Fake:
        def forecast(self, **kwargs):
            assert kwargs['context'].shape == (2, 1, 90)
            assert kwargs['past_covariates'].shape == (2, 2, 90)
            assert kwargs['prediction_length'] == 30
            assert kwargs['symmetric_averaging'] and kwargs['clip_nonnegative']
            assert 'known_covariates' not in kwargs
            class Out:
                median = np.full((2, 1, 30), -1.)
            return Out()
    result = TimestralAdapter(Fake()).forecast(np.zeros((2, 90)), np.zeros((2, 90, 2)))
    assert (result['forecast'] == 0).all()
    assert result['n_values_clipped'] == [30, 30]


def test_fitting_and_single_class():
    x = np.arange(240.).reshape(8, 30)
    y = np.array([0, 1] * 4)
    model = fit_forecast_mapper(x, y)
    assert model.predict_proba(x).shape == (8, 2)
    with pytest.raises(ValueError):
        fit_forecast_mapper(x, np.zeros(8))
    topology = np.arange(40.).reshape(8, 5)
    model, c, scores = fit_topology_logistic(topology, y, topology, y, [1] * 4 + [2] * 4)
    assert c in (0.1, 1, 10)
    assert len(scores) == 3
    assert model.predict_proba(topology).shape == (8, 2)


def test_loader_rejects_unpinned_source(monkeypatch):
    import cooperalink.models as models
    monkeypatch.setattr(models, '_source_revision', lambda: None)
    with pytest.raises(RuntimeError, match='source revision'):
        models.load_timestral()


def test_timestral_retries_out_of_memory_by_splitting():
    class Fake:
        def forecast(self, **kwargs):
            n = len(kwargs['context'])
            if n > 1:
                raise RuntimeError('CUDA out of memory')
            class Out:
                median = np.ones((n, 1, 30))
            return Out()
    result = TimestralAdapter(Fake()).forecast(np.zeros((3, 90)))
    assert result['status'] == ['ok'] * 3


def test_classical_records_warnings_and_diagnostics():
    import warnings
    def backend(series):
        warnings.warn('informational warning')
        return np.ones(30)
    result = forecast_classical('arima', np.arange(90).reshape(1, 90), '2023-01-01', backend=backend)
    assert result['warnings'] == [['informational warning']]
    assert isinstance(result['diagnostics'][0], dict)


def test_arima_forecasts_sparse_history_after_optimizer_nonconvergence():
    counts = np.zeros((1, 90), dtype=np.float32)
    counts[0, 43:46] = [2, 3, 2]
    result = forecast_classical("arima", counts, "2023-07-29")
    assert result["status"] == ["ok"]
    assert result["forecast"].shape == (1, 30)
    assert np.isfinite(result["forecast"]).all()
    attempts = result["diagnostics"][0]["optimizer_attempts"]
    assert attempts[0]["solver"] == "default"
    assert attempts[-1]["converged"] is True
    if len(attempts) > 1:
        assert [entry["solver"] for entry in attempts] == ["default", "bfgs"]
        assert attempts[0]["converged"] is False
