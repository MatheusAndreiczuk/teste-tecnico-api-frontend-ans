import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Operadoras from './views/Operadoras.vue'
import OperadoraDetalhe from './views/OperadoraDetalhe.vue'
import Estatisticas from './views/Estatisticas.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/operadoras', name: 'Operadoras', component: Operadoras },
  { path: '/operadoras/:cnpj', name: 'OperadoraDetalhe', component: OperadoraDetalhe },
  { path: '/estatisticas', name: 'Estatisticas', component: Estatisticas }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
