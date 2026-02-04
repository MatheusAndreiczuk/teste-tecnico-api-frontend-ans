import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.response.use(
  response => response,
  error => {
    const message = error.response?.data?.detail || 'Erro ao conectar com o servidor'
    return Promise.reject(new Error(message))
  }
)

export default {
  async getOperadoras(params = {}) {
    const response = await api.get('/operadoras', { params })
    return response.data
  },

  async getOperadora(cnpj) {
    const response = await api.get(`/operadoras/${cnpj}`)
    return response.data
  },

  async getDespesasOperadora(cnpj, params = {}) {
    const response = await api.get(`/operadoras/${cnpj}/despesas`, { params })
    return response.data
  },

  async getEstatisticas() {
    const response = await api.get('/estatisticas')
    return response.data
  }
}
