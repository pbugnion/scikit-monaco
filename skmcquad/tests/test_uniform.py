
import numpy as np
from numpy.testing import TestCase, run_module_suite

from skmcquad.uniform import mcquad

HALF_ROOT_PI = 0.5*np.sqrt(np.pi)

class TestMCQuad(TestCase):
    """
    The expected variance for N integration points is:

    (<f^2> - <f>^2) / N 

    where <.> denotes the integration of function f.
    """

    def setUp(self):
        self.gaussian = lambda x: np.exp(-sum(x**2))

    def run_serial(self,f,npoints,expected_value,expected_variance,**kwargs):
        res, sd = mcquad(f,npoints,nprocs=1,**kwargs)
        error = np.sqrt(expected_variance/float(npoints))
        self.assertTrue(within_tol(res,expected_value,3.*max(error,1e-10)))
        self.assertTrue(within_tol(sd,error,0.1*max(error,1e-10)))

    def run_parallel(self,f,npoints,expected_value,expected_variance,**kwargs):
        batch_size = npoints/10
        res, sd = mcquad(f,npoints,nprocs=2,batch_size=batch_size,**kwargs)
        error = np.sqrt(expected_variance/float(npoints))
        self.assertTrue(within_tol(res,expected_value,3.*max(error,1e-10)))
        self.assertTrue(within_tol(sd,error,0.1*max(error,1e-10)))

    def run_all(self,f,npoints,expected_value,expected_variance,**kwargs):
        self.run_serial(f,npoints,expected_value,expected_variance,**kwargs)
        self.run_parallel(f,npoints,expected_value,expected_variance,**kwargs)

    def const(self,x):
        """
        Constant function.

        <f> = 1.0
        <(f - <f>)^2> = 0.0
        """
        return 1.0

    def prod(self,x):
        """
        Product_i x_i.

        If the integral region is between 0 and 1:

        <f> = 1/2^d
        <(f-<f>)^2> = (1/3)^d - 1/2^(d-1)+1
        """
        return np.multiply.reduce(x)

    def prod_variance(self,d):
        """ 
        Variance of the function Product_i x_i as a function of the 
        dimensionality.
        """
        return (1./3.**d) - 0.25**d

    def test_const_1d(self):
        """
        Constant function between 0 and 1.

        Value : 1.
        Variance : 0.
        """
        self.run_all(self.const,2000,1.,0.,xl=[0.],xu=[1.])

    def test_const_1db(self):
        """
        Constant function between -1 and 2.

        Value: 3.
        Variance 0.
        """
        self.run_all(self.const,2000,3.0,0.0,xl=[-1.],xu=[2.])

    def test_const_6d(self):
        """
        Constant function between -1. and 2. in six dimensions.

        Value: 3**6
        Variance: 0.
        """
        self.run_all(self.const,20000,3.0**6,0.0,xl=[-1.]*6,xu=[2.]*6)

    def test_gaussian1d(self):
        pass

    def test_prod1d(self):
        """ f(x) = x between 0 and 1. """
        npoints = 2000
        variance = self.prod_variance(1)
        self.run_all(self.prod,npoints,0.5,variance,xl=[0.],xu=[1.])

    def test_prod2d(self):
        """ f(x,y) = x*y between 0 and 1. """
        npoints = 2000
        variance = self.prod_variance(2)
        self.run_all(self.prod,npoints,0.25,variance,xl=[0.,0.],xu=[1.,1.])

    def test_prod6d(self):
        """ f(x,...) = product_1..6 x_i between 0 and 1. """
        npoints = 50000
        variance = self.prod_variance(6)
        self.run_all(self.prod,npoints,0.5**6,variance,xl=[0.]*6,xu=[1.]*6)

    def test_wrong_xl(self):
        """
        Raise a ValueError if len(xl) != len(xu).
        """
        with self.assertRaises(ValueError):
            mcquad(self.const,2000,xl=[0.,0.],xu=[1.])

    def test_wrong_nprocs(self):
        """
        Raise a ValueError if nprocs < 1
        """
        with self.assertRaises(ValueError):
            mcquad(self.const,2000,xl=[0.],xu=[1.],nprocs=-1)

    def test_wrong_npoints(self):
        """
        Raise a ValueError if npoints < 2.
        """
        with self.assertRaises(ValueError):
            mcquad(self.const,0,xl=[0.],xu=[1.])

    def test_wrong_seed(self):
        """
        Raise a TypeError if seed is not a list.
        """
        with self.assertRaises(TypeError):
            mcquad(self.const,2000,xl=[0.],xu=[1.],seed=1234)



def within_tol(a,b,tol):
    return np.abs(a-b).max() < tol

if __name__ == '__main__':
    run_module_suite()