"""Helper routines for accessing HDF5 output of ScannerBit"""

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pyscannerbit.plottools as pt

# Helper class to manage data/is_valid HDF5 dataset pairs 
class DataPair:
  def __init__(self,g,name,model=None):
     try:
         self._valid = g["{}_isvalid".format(name)]
     except KeyError:
         name = "{}::{}".format(model, name)
         self._valid = g["{}_isvalid".format(name)]
     self._data  = g[name]
  
  def data(self):
     return self._data

  def valid(self):
     return np.array(self._valid, dtype=np.bool)

  def validdata(self):
     return self.data()[self.valid()]


def get_data(in_group, hdf5_dataset_names, apply_common_mask=True, model=None):
  datapairs = []
  for name in hdf5_dataset_names:
    datapairs += [ DataPair(in_group,name,model) ]
  output = [] 
  if apply_common_mask:
     m = datapairs[0].valid()
     for d in datapairs[1:]:
        m = m & d.valid()
     for d in datapairs:
        output += [d.data()[m]]
  else:
     output = datapairs
  return output


class HDF5(h5py.Group):
    """
    Class representing HDF5 results from ScannerBit
    ===============================================
    """
    def __init__(self, group, model=None, loglike="LogLike", posterior="Posterior"):
        """
        """
        self.loglike = loglike
        self.posterior = posterior
        super().__init__(group)
        self.model = model if model else self.get_model_name()

    def get_model_name(self):
        """
        """
        for k in self.keys():
            if "::" in k:
                return k.split("::")[0]

    def get_param_names(self):
        """
        """
        prefix = "{}::".format(self.model)
        suffix = "_isvalid"
        return [k[len(prefix):] for k in self.keys()
            if k.startswith(prefix) and not k.endswith(suffix)]

    def get_params(self, names):
        return get_data(self, names, model=self.model, apply_common_mask=True)

    def get_param(self, name):
        return get_data(self, [name], model=self.model, apply_common_mask=True)[0]

    def get_loglike(self):
        """
        """
        return self.get_param(self.loglike)

    def get_posterior(self):
        """
        """
        return self.get_param(self.posterior)

    def get_best_fit(self, name):
        """
        """
        loglike = self.get_loglike()
        index = np.argmax(loglike)
        return self.get_param(name)[index]

    def get_min_chi_squared(self):
        """
        """
        return -2. * self.get_loglike().max()

    def make_plot(self, name_x, name_y):
        """
        """
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)

        ax.scatter(self.get_param(name_x), self.get_param(name_y),
          marker="o", facecolor='k', edgecolor='', alpha=0.5, s=20)
        ax.scatter(self.get_best_fit(name_x), self.get_best_fit(name_y),
          marker="*", facecolor='Gold', alpha=1., s=250, label="Best-fit")

        ax.set_xlabel(name_x)
        ax.set_ylabel(name_y)
        ax.legend()
        plt.show()

    def plot_profile_likelihood(self,ax,xpar,ypar,use_default_model_name=True):
        if(use_default_model_name):
           xpar = "{0}::{1}".format(self.model,xpar)
           ypar = "{0}::{1}".format(self.model,ypar)
        logl,x,y = get_data(self,[self.loglike,xpar,ypar])
        mask = logl.valid() & x.valid() & y.valid()
        data = np.vstack((x.data()[mask],
                          y.data()[mask],
                       -2*logl.data()[mask])).T
        pt.profplot(ax,data,title=None,labels=[xpar,ypar],nxbins=50,nybins=50)

