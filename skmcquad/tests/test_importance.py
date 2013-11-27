
import numpy as np
from numpy.testing import TestCase, run_module_suite, build_err_msg
from numpy.random import exponential,uniform

from skmcquad import mcimport

class TestMCImport(TestCase):
    """
    The expected variance for N integration points is,
    if the function is f and the probability distribution is g:

    sqrt{int f^2 * g dx - (int f*g dx)^2 / N}
    """

    def setUp(self):
        pass

    def exp_integral(self,d):
        return (1.-np.exp(-1))**d

    def exp_variance(self,d):
        return self.exp_integral(d) - self.exp_integral(d)**2

    def run_serial(self,f,npoints,distribution,expected_value,expected_variance,**kwargs):
        res,sd = mcimport(f,npoints,distribution,nprocs=1,**kwargs)
        error = np.sqrt(expected_variance/float(npoints))
        assert_within_tol(res,expected_value,3.*max(error,1e-10),
            "Error in <f> in serial run.")
        assert_within_tol(sd,error,0.1*max(error,1e-10),
            "Error in expected error in serial run.")

    def run_parallel(self,f,npoints,distribution,expected_value,expected_variance,**kwargs):
        res,sd = mcimport(f,npoints,distribution,nprocs=2,**kwargs)
        error = np.sqrt(expected_variance/float(npoints))
        assert_within_tol(res,expected_value,3.*max(error,1e-10),
            "Error in <f> in parallel run.")
        assert_within_tol(sd,error,0.1*max(error,1e-10),
            "Error in expected error in parallel run.")

    def run_all(self,f,npoints,distribution,expected_value,expected_variance,**kwargs):
        self.run_serial(f,npoints,distribution,expected_value,expected_variance,**kwargs)
        self.run_parallel(f,npoints,distribution,expected_value,expected_variance,**kwargs)

    def test_exp_1d(self):
        """
        e^-x for x = 0..1 with g(x) = e^-x
        """
        npoints = 2000
        self.run_all(lambda x:x<1.0,npoints,exponential,
                self.exp_integral(1),self.exp_variance(1))

    def test_exp_1db(self):
        """
        e^-x for x = 0..1 with g(x) = e^-x : alternate dist formulation
        """
        npoints = 2000
        self.run_all(lambda x:x<1.0,npoints,lambda size: exponential(size=(size,1)),
                self.exp_integral(1),self.exp_variance(1))

    def test_exp_2d(self):
        """
        e^-(x+y) for x,y = 0..1 with g(x) = e^-(x+y)
        """
        npoints = 2000
        self.run_all(lambda (x,y):x<1.0 and y<1.0,npoints,
                lambda size:(exponential(size=(size,2))),
                self.exp_integral(2),self.exp_variance(2))

    def test_exp_6d(self):
        """
        e^-(sum(x)) for x = 0..1 with g(x) = e^-(sum(x)) for d=6.
        """
        npoints = 10000
        self.run_all(lambda x:np.all(x<1.0),npoints,
                lambda size:(exponential(size=(size,6))),
                self.exp_integral(6),self.exp_variance(6))

    def test_mixed_distributions(self):
        """
        exp^(-x)*y**2 for x,y = 0..1 with g(x) ~ Exp and g(y) ~ U[0,1]
        """
        npoints = 2000
        def dist(size):
            xs = exponential(size=size)
            ys = uniform(size=size)
            return np.array((xs,ys)).T
        self.run_all(lambda (x,y):y**2*(x<1.),npoints,dist,
                self.exp_integral(1)/3.,
                self.exp_integral(1)/5.-(self.exp_integral(1)**2)/9.)

    def test_weight(self):
        """
        Weight 'exp^(-x)' by 2.0.
        """
        npoints = 2000
        self.run_all(lambda x: x<1.0,npoints,exponential,
                2.0*self.exp_integral(1),4.0*self.exp_variance(1),weight=2.0)

    def test_args(self):
        """
        a*exp(-x) where a is an "arg" passed to f.
        """
        npoints = 2000
        aval = 2.0
        self.run_all(lambda x,a: a*(x<1.0), npoints,exponential,
                aval*self.exp_integral(1),aval**2*self.exp_variance(1),
                args=(aval,))

    def test_dist_kwargs(self):
        """
        exp(-x/c) where c is an "arg" passed to g.
        """
        npoints = 2000
        cval = 2.0
        exp_integral = cval*(1.-np.exp(-1./cval))
        self.run_all(lambda x:cval*(x<1.0), npoints, exponential,
                exp_integral,cval*exp_integral-exp_integral**2,
                dist_kwargs=dict(scale=cval))

    def test_seed(self):
        """
        Test same seed -> same result.
        """
        npoints = 50000
        res,error = mcimport(lambda x: x<1.0,npoints,exponential,seed=[1234,5678])
        res2, error2 = mcimport(lambda x: x<1.0,npoints,exponential,seed=[1234,5678])
        assert res == res2
        assert error == error2

    def test_seed_different(self):
        """
        Test different seed -> different result.
        """
        npoints = 50000
        res,error = mcimport(lambda x: x<1.0,npoints,exponential,seed=[1234,5678])
        res2, error2 = mcimport(lambda x: x<1.0,npoints,exponential,seed=[1235,5678])
        assert res != res2
        assert error != error2
                

#FIXME refactor
def within_tol(a,b,tol):
    return np.abs(a-b).max() < tol

def assert_within_tol(a,b,tol,err_msg=""):
    if not within_tol(a,b,tol):
        msg = build_err_msg((a,b),err_msg)
        raise AssertionError(msg)

if __name__ == '__main__':
    run_module_suite()