import sys
from importlib.metadata import version
from importlib.util import find_spec

import numpy as np
import pytest

from elisa import BayesFit, MaxLikeFit
from elisa.models import PowerLaw

JAXNS_XFAIL_MARK = pytest.mark.xfail(
    not bool(find_spec('jaxns'))
    and sys.version_info >= (3, 13)
    or (
        version('jaxns') == '2.6.7'
        and tuple(map(int, version('jax').split('.'))) >= (0, 6, 0)
    ),
    reason='jaxns==2.6.7 is incompatible with jax>=0.6.0 or python>=3.13',
)


@pytest.mark.parametrize(
    'method',
    [
        pytest.param('minuit', id='iminuit'),
        pytest.param('lm', id='optimistix.LevenbergMarquardt'),
        pytest.param('ns', marks=JAXNS_XFAIL_MARK, id='JAXNS'),
    ],
)
def test_trivial_max_like_fit(simulation, method):
    data = simulation
    model = PowerLaw(alpha=0.0)
    result = MaxLikeFit(data, model).mle(method=method)

    # Check that the fit result is correct,
    # note that the analytic result is known for alpha = 0 and uniform egrid
    mle_fit, err_fit = result.mle['PowerLaw.K']
    mle_analytic = np.mean(data.ce)
    nbins = data.resp_data.channel_number
    spec_exposure = data.spec_exposure
    de = np.diff(data.resp_data.photon_egrid)[0]
    err_analytic = np.sqrt(mle_analytic / nbins / spec_exposure / de)
    ci = result.ci().errors['PowerLaw.K']

    assert np.isclose(mle_fit, mle_analytic)
    assert np.isclose(err_fit, err_analytic)
    assert np.isclose(ci[0], -err_analytic, rtol=5e-3, atol=0)
    assert np.isclose(ci[1], err_analytic, rtol=5e-3, atol=0)


@pytest.mark.parametrize(
    'method, options',
    [
        # NumPyro samplers
        pytest.param('nuts', {}, id='NUTS'),
        pytest.param('barkermh', {}, id='BarkerMH'),
        pytest.param('blackjax_nuts', {}, id='BlackJAX_NUTS'),
        pytest.param('sa', {'warmup': 20000}, id='SA'),
        pytest.param('aies', {}, id='AIES'),
        pytest.param('aies', {'n_parallel': 1}, id='AIES_1'),
        pytest.param('ess', {}, id='ESS'),
        pytest.param('ess', {'n_parallel': 1}, id='ESS_1'),
        # JAX backend nested sampler
        pytest.param('jaxns', {}, marks=JAXNS_XFAIL_MARK, id='JAXNS'),
        # Non-JAX backends samplers
        pytest.param('emcee', {}, id='emcee'),
        pytest.param('emcee', {'n_parallel': 1}, id='emcee_1'),
        pytest.param('zeus', {'steps': 2000}, id='zeus'),
        pytest.param('zeus', {'steps': 2000, 'n_parallel': 1}, id='zeus_1'),
        # Non-JAX backends nested samplers
        pytest.param('nautilus', {}, id='Nautilus'),
        pytest.param('ultranest', {}, id='UltraNest'),
    ],
)
def test_trivial_bayes_fit(simulation, method, options):
    data = simulation
    model = PowerLaw()
    model.PowerLaw.K.log = True

    # SA seems to converge randomly, which is really frustrating
    # we try to fix this by better init and seed of 100...
    if method == 'sa':
        model['PowerLaw']['alpha'].default = 0.0
        model['PowerLaw']['K'].default = 10.0

    # check the global random state of numpy is unaffected after the fit
    np.random.seed(0)
    test_rand = np.random.rand()
    np.random.seed(0)

    fit_fn = getattr(BayesFit(data, model, seed=100), method)

    # Bayesian fit result, i.e. posterior
    result = fit_fn(**options)

    # test refit with given post_warmup_state
    if result.sampler_state is not None:
        options['steps'] = 100
        fit_fn(post_warmup_state=result.sampler_state, **options)

    # check convergence
    assert all(i < 1.01 for i in result.rhat.values() if not np.isnan(i))

    # check the true parameters values are within the 68% CI
    ci = result.ci(cl=1).intervals
    assert ci['PowerLaw.K'][0] < 10.0 < ci['PowerLaw.K'][1]
    assert ci['PowerLaw.alpha'][0] < 0.0 < ci['PowerLaw.alpha'][1]

    # check the global random state of numpy is unaffected after the fit
    assert np.allclose(np.random.rand(), test_rand)
