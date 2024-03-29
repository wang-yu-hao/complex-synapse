import numpy as np 
import scipy
import matplotlib.pyplot as plt
import numpy.random as random
import matplotlib.pyplot as plt
import matplotlib.cm as cm


class Log:
    def __init__(self, neuron, sigma_s, epsilon, sigma_y, tau_u, tau_y, tau_z, u_mode, y_mode, z_mode, T, dt):
        self.env_parameters = dict(
            sigma_s = sigma_s,
            epsilon = epsilon,
            sigma_y = sigma_y,
            tau_u = tau_u,
            tau_y = tau_y,
            tau_z = tau_z,
            u_mode = u_mode,
            y_mode = y_mode,
            z_mode = z_mode,
            T = T,
            dt = dt
        )
        self.timeline = np.arange(0, T, dt)
        length = len(self.timeline)
        self.s = np.zeros(length)
        self.u = np.zeros((length, neuron.N, 1))
        self.v = np.zeros(length)
        self.y = np.zeros((length, neuron.N, 1))
        self.z = np.zeros((length, neuron.N, 1))
        # self.orthog = np.zeros((length, neuron.N, 1))
        self.W = np.zeros((length, neuron.S, neuron.N))
        # self.w = np.zeros((length, neuron.N, 1))
        # self.w_norm = np.zeros(length)
        # self.w_para = np.zeros(length)
        # self.w_orthog = np.zeros(length)
        self.po = np.zeros((length, neuron.S, 1))

    def __repr__(self):
        return '{}'.format(
            self.env_parameters
        )


class Neuron:
    def __init__(self, N, S, tau_W, beta, gamma=1, phi=100, psi=100, n_C=2, n_g=2, alpha=1):
        self.hyper = dict(
            N = N,
            S = S,
            tau_W = tau_W,
            beta = beta,
            gamma = gamma,
            phi = phi,
            psi = psi,
            n_C = n_C,
            n_g = n_g,
            alpha = alpha
        )
        self.e1 = np.zeros((S, 1))
        self.e1[0,0] = 1
        # self.P = self.e1 @ (self.e1.T)
        self.po = np.reshape(scipy.special.softmax(-phi * np.arange(S)), (S,1))
        self.pi = np.reshape(scipy.special.softmax(-psi * np.arange(S)), (S,1))
        self.P = self.pi @ (self.po.T)
        self.N = N
        self.S = S
        self.tau_W = tau_W
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.L = np.zeros((S, S))
        for a in range(S):
            self.L[a, a] = -beta * ((n_C * n_g) ** (-(a+1)) * n_C * (n_g + 1))
            if a == 0:
                self.L[a, a] = -beta * ((n_C * n_g) ** (-(a+1)) * n_C)
            if a != 0:
                self.L[a, a-1] = gamma * beta * ((n_C * n_g) ** (-(a+1) + 1))
            if a != S-1:
                self.L[a, a+1] = gamma * beta * ((n_C ** (-2*(a+1) + 1)))

        '''Original Benna-Fusi model'''
        # for a in range(S):
        #     self.L[a, a] = -beta * (n_C ** (-2*(a+1) + 1) * (n_C + 1))
        #     if a == 0:
        #         self.L[a, a] = -beta * (n_C ** (-2*(a+1) + 1))
        #     if a != 0:
        #         self.L[a, a-1] = gamma * beta * (n_C ** (-2*(a+1) + 2))
        #     if a != S-1:
        #         self.L[a, a+1] = gamma * beta * (n_C ** (-2*(a+1) + 1))

        self.W0 = random.randn(S, N) / np.sqrt(N) * 0.01
        self.W = self.W0
        self.w = self.W.T @ self.e1
        self.logs = []

    def __repr__(self):
        output = 'Properties: {}.\nTrials: \n'.format(self.hyper)
        if len(self.logs) != 0:
            for i in range(len(self.logs)):
                if type(self.logs[i]) == tuple:
                    output += '{}: {}. \n'.format(i, self.logs[i][0])
                else:
                    output += '{}: {}. \n'.format(i, self.logs[i].env_parameters)
        return output
        
    
    def plot(self):
        pass

    def reinitialise(self, scale=0.01):
        self.W0 = random.randn(self.S, self.N)  / np.sqrt(self.N) * scale
        return

    def eigvals_L(self):
        return np.sort(np.linalg.eigvals(self.L)) / self.tau_W

    def timescales_L(self):
        return (-1) / self.eigvals_L()

    def eigvals_whole(self, log=None, C=None):
        if not C:
            C = log.env_parameters['sigma_s'] ** 2 * (log.y[-1] @ log.y[-1].T) + log.env_parameters['epsilon'] ** 2 * np.eye(self.N)

        eigvals_C = np.sort(np.linalg.eigvals(C))[::-1]

        if self.L.shape == (1, 1):
            if self.L == np.array([[0]]):
                chi = 0
            else:
                # chi = 1 / (np.linalg.inv(self.L)[0,0])
                chi = 1 / (self.po.T @ np.linalg.inv(self.L) @ self.pi).item()

        else:
            # chi = 1 / (np.linalg.inv(self.L)[0,0])
            chi = 1 / (self.po.T @ np.linalg.inv(self.L) @ self.pi).item()


        eigvals_sys = []

        l_til = -2 * eigvals_C[0] - 3 * chi 
        # print(l_til)
        L = self.L + l_til * self.P
        eigvals_sys.append(np.sort(np.linalg.eigvals(L)))

        for l in eigvals_C[1:]:
            l_til = l - eigvals_C[0] - chi
            # print(l_til)
            L = self.L + l_til * self.P
            eigvals_sys.append(np.sort(np.linalg.eigvals(L)))

        eigvals_sys = np.array(eigvals_sys)

        return eigvals_sys / self.tau_W

    def timescales_whole(self, log=None, C=None):
        return  (-1) / self.eigvals_whole(log=log, C=C)

    def eigvecs_whole(self, log=None, C=None):
        if not C:
            C = log.env_parameters['sigma_s'] ** 2 * (log.y[-1] @ log.y[-1].T) + log.env_parameters['epsilon'] ** 2 * np.eye(self.N)

        w, v = np.linalg.eig(C)
        eigvals_C = np.sort(w)[::-1]
        eigvecs_C = v[:, np.argsort(w)[::-1]]
        # chi = 1 / (np.linalg.inv(self.L)[0,0])
        chi = 1 / (self.po.T @ np.linalg.inv(self.L) @ self.pi).item()

        eigvals_sys = []
        eigvecs_sys = []

        l_til = -2 * eigvals_C[0] - 3 * chi 
        # print(l_til)
        L = self.L + l_til * self.P
        # eigvals_sys.append(np.sort(np.linalg.eigvals(L)))
        w, v = np.linalg.eig(L)
        v = v[:, np.argsort(w)]
        eigvecs = []
        for i in range(self.S):
            eigvecs.append(v[:, [i]] @ eigvecs_C[:, [0]].T)

        eigvecs = np.array(eigvecs)
        eigvecs_sys.append(eigvecs)

        for i, l in enumerate(eigvals_C[1:], start=1):
            l_til = l - eigvals_C[0] - chi
            # print(l_til)
            L = self.L + l_til * self.P
            eigvals_sys.append(np.sort(np.linalg.eigvals(L)))

            w, v = np.linalg.eig(L)
            v = v[:, np.argsort(w)]
            eigvecs = []
            for i in range(self.S):
                eigvecs.append(v[:, [i]] @ eigvecs_C[:, [0]].T)

            eigvecs = np.array(eigvecs)
            eigvecs_sys.append(eigvecs)

        eigvecs_sys = np.array(eigvecs_sys)

        print(eigvecs_sys.shape)

        fig, axs = plt.subplots(self.N, self.S, squeeze=True, figsize=(20, 20))

        for i in range(self.N):
            for j in range(self.S):
                axs[i, j].imshow(eigvecs_sys[i, j, :, :], cmap=cm.Greys_r)

        fig.show()
        fig.tight_layout()

        return

    @staticmethod
    def make_neurons():
        return

