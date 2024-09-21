"""WARNING: this program only work on MacOS or Linux. You must have CMake and a C compiler.
please install `NumbaQuadpack` before running
https://github.com/xiesl97/NumbaQuadpack



`QUADPACK` is a FORTRAN 77 library for numerical integration of one-dimensional functions.
see introdution https://en.wikipedia.org/wiki/QUADPACK

`CQUADPACK` includes a complete port of the QUADPACK Fortran codes to C.
https://github.com/ESSS/cquadpack

`NumbaQuadpack` is a python wrapper to cquadpack.
https://github.com/Nicholaswogan/NumbaQuadpack

@Nicholaswogan/NumbaQuadpack only support definite integrals `dqags`.
this program supports infinite integrals `dqagi`.
simple adaptive integrator `dqag`.
non-adaptive integrator `dqng`.
please install @xiesl97/NumbaQuadpack before running
https://github.com/xiesl97/NumbaQuadpack

if you want other routines in `QUADPACK`,
you can fork `NumbaQuadpack` and write code self

"""

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numba as nb
import numpy as np
from NumbaQuadpack import dqag, dqagi, dqags, dqng, quadpack_sig


class QuadpackTransform:
    def __init__(self, fun):
        self._fun = fun

    def _cfun(self, n=0):
        fun = self._fun

        if n == 0:
            cfun = lambda x, _data: fun(x)
        else:

            def cfun(x, _data):
                data = nb.carray(_data, (n,))
                return fun(x, data)

        return nb.cfunc(quadpack_sig)(cfun).address

    @staticmethod
    def _dqags(cfun, vectorized=False):
        @jax.jit
        def _dqags_call(
            a,
            b,
            data=jnp.asarray([0.0], jnp.float64),
            epsabs=1.49e-08,
            epsrel=1.49e-08,
        ):
            a, b = jnp.float64(a), jnp.float64(b)
            epsabs, epsrel = jnp.float64(epsabs), jnp.float64(epsrel)
            data = jnp.asarray(data)

            def _pcb(a, b, data, epsabs, epsrel):
                a, b, epsabs, epsrel = (
                    np.float64(a),
                    np.float64(b),
                    np.float64(epsabs),
                    np.float64(epsrel),
                )
                data = np.asarray(data)
                sol, abserr, success = dqags(cfun, a, b, data, epsabs, epsrel)
                return np.asarray([sol, abserr, success], dtype=np.float64)

            result_shape_dtype = jax.ShapeDtypeStruct(shape=(3,), dtype=jnp.float64)
            return jax.pure_callback(
                _pcb,
                result_shape_dtype,
                a,
                b,
                data,
                epsabs,
                epsrel,
                vectorized=vectorized,
            )

        return _dqags_call

    @staticmethod
    def _dqng(cfun, vectorized=False):
        @jax.jit
        def _dqng_call(
            a,
            b,
            data=jnp.asarray([0.0], jnp.float64),
            epsabs=1.49e-08,
            epsrel=1.49e-08,
        ):
            a, b = jnp.float64(a), jnp.float64(b)
            epsabs, epsrel = jnp.float64(epsabs), jnp.float64(epsrel)
            data = jnp.asarray(data)

            def _pcb(a, b, data, epsabs, epsrel):
                a, b, epsabs, epsrel = (
                    np.float64(a),
                    np.float64(b),
                    np.float64(epsabs),
                    np.float64(epsrel),
                )
                data = np.asarray(data)
                sol, abserr, success = dqng(cfun, a, b, data, epsabs, epsrel)
                return np.asarray([sol, abserr, success], dtype=np.float64)

            result_shape_dtype = jax.ShapeDtypeStruct(shape=(3,), dtype=jnp.float64)
            return jax.pure_callback(
                _pcb,
                result_shape_dtype,
                a,
                b,
                data,
                epsabs,
                epsrel,
                vectorized=vectorized,
            )

        return _dqng_call

    @staticmethod
    def _dqag(cfun, vectorized=False):
        @jax.jit
        def _dqag_call(
            a,
            b,
            data=jnp.asarray([0.0], jnp.float64),
            epsabs=1.49e-08,
            epsrel=1.49e-08,
            irule=1,
        ):
            a, b = jnp.float64(a), jnp.float64(b)
            epsabs, epsrel = jnp.float64(epsabs), jnp.float64(epsrel)
            irule = jnp.int32(irule)
            data = jnp.asarray(data)

            def _pcb(a, b, data, epsabs, epsrel, irule):
                a, b, epsabs, epsrel = (
                    np.float64(a),
                    np.float64(b),
                    np.float64(epsabs),
                    np.float64(epsrel),
                )
                irule = np.int32(irule)
                data = np.asarray(data)
                sol, abserr, success = dqag(cfun, a, b, data, epsabs, epsrel, irule)
                return np.asarray([sol, abserr, success], dtype=np.float64)

            result_shape_dtype = jax.ShapeDtypeStruct(shape=(3,), dtype=jnp.float64)
            return jax.pure_callback(
                _pcb,
                result_shape_dtype,
                a,
                b,
                data,
                epsabs,
                epsrel,
                irule,
                vectorized=vectorized,
            )

        return _dqag_call

    @staticmethod
    def _dqagi(cfun, vectorized=False):
        @jax.jit
        def _dqagi_call(
            a,
            b,
            data=jnp.asarray([0.0], jnp.float64),
            epsabs=1.49e-08,
            epsrel=1.49e-08,
        ):
            a, b = jnp.float64(a), jnp.float64(b)
            epsabs, epsrel = jnp.float64(epsabs), jnp.float64(epsrel)
            data = jnp.asarray(data)

            def _pcb(a, b, data, epsabs, epsrel):
                if np.isneginf(a) and np.isposinf(b):
                    a, b = 0, 2
                elif ~np.isneginf(a) and np.isposinf(b):
                    a, b = np.float64(a), 1
                elif np.isneginf(a) and ~np.isposinf(b):
                    a, b = np.float64(b), -1
                else:
                    raise ValueError(f"dqagi can not integrate from {a} to {b}")
                epsabs, epsrel = np.float64(epsabs), np.float64(epsrel)
                data = np.asarray(data)
                sol, abserr, success = dqagi(cfun, a, b, data, epsabs, epsrel)
                return np.asarray([sol, abserr, success], dtype=np.float64)

            result_shape_dtype = jax.ShapeDtypeStruct(shape=(3,), dtype=jnp.float64)
            return jax.pure_callback(
                _pcb,
                result_shape_dtype,
                a,
                b,
                data,
                epsabs,
                epsrel,
                vectorized=vectorized,
            )

        return _dqagi_call


if __name__ == "__main__":
    import numpyro

    numpyro.set_platform("cpu")
    """example 1
        definite intervals
    """

    @nb.njit
    def f(x, data):
        (
            y,
            z,
            d,
        ) = data
        return np.exp(-(x**2)) + y + z * d

    a = jnp.float64(0.0)
    b = jnp.float64(1.0)
    data = jnp.asarray([2.0, 3.0, 4.0], dtype=jnp.float64)
    qt = QuadpackTransform(f)
    cfun = qt._cfun(n=3)  # length of data in `f`
    func_dqags = jax.jit(qt._dqags(cfun, vectorized=False))
    print(func_dqags(a, b, data))

    """example 2
        infinite intervals
    """

    @nb.njit
    def f1(
        x,
    ):
        return np.exp(-x)

    a = jnp.float64(0.0)
    b = jnp.inf
    qt1 = QuadpackTransform(f1)
    cfun1 = qt1._cfun(n=0)
    func_dqagi = jax.jit(qt._dqagi(cfun1, vectorized=False))
    print(
        func_dqagi(
            a,
            b,
        )
    )

    """example 3
        definite intervals
        simple adaptive integrator

        irule - integration rule to be used as follows:
            irule = 1 -- G_K 7-15
            irule = 2 -- G_K 10-21
            irule = 3 -- G_K 15-31
            irule = 4 -- G_K 20-41
            irule = 5 -- G_K 25-51
            irule = 6 -- G_K 30-61

    """

    @nb.njit
    def f(x, data):
        (
            y,
            z,
            d,
        ) = data
        return np.exp(-(x**2)) + y + z * d

    a = jnp.float64(0.0)
    b = jnp.float64(1.0)
    data = jnp.asarray([2.0, 3.0, 4.0], dtype=jnp.float64)
    qt = QuadpackTransform(f)
    cfun = qt._cfun(n=3)  # length of data in `f`
    func_dqag = jax.jit(qt._dqag(cfun, vectorized=False))
    print(func_dqag(a, b, data))

    """example 4
        definite intervals
        simple non-adaptive integrator
        a little more accuracy than trapezoidal
        but not recommend

    """

    @nb.njit
    def f(x, data):
        (
            y,
            z,
            d,
        ) = data
        return np.exp(-(x**2)) + y + z * d

    a = jnp.float64(0.0)
    b = jnp.float64(1.0)
    data = jnp.asarray([2.0, 3.0, 4.0], dtype=jnp.float64)
    qt = QuadpackTransform(f)
    cfun = qt._cfun(n=3)  # length of data in `f`
    func_dqng = jax.jit(qt._dqng(cfun, vectorized=False))
    print(func_dqng(a, b, data))
