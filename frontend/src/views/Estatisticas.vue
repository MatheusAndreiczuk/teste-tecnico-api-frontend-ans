<template>
  <div>
    <h2 class="mb-4">Estatísticas</h2>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Carregando...</span>
      </div>
      <p class="mt-2">Carregando estatísticas...</p>
    </div>

    <div v-else-if="error" class="alert alert-danger">
      <strong>Erro:</strong> {{ error }}
      <button class="btn btn-sm btn-outline-danger ms-3" @click="fetchEstatisticas">
        Tentar novamente
      </button>
    </div>

    <div v-else-if="stats">
      <div class="row g-3 mb-4">
        <div class="col-6 col-lg-3">
          <div class="card text-center bg-primary text-white h-100">
            <div class="card-body py-3">
              <h3 class="mb-1">{{ stats.gerais.total_operadoras }}</h3>
              <p class="mb-0 small">Operadoras</p>
            </div>
          </div>
        </div>
        <div class="col-6 col-lg-3">
          <div class="card text-center bg-success text-white h-100">
            <div class="card-body py-3">
              <h3 class="mb-1">{{ formatCurrencyShort(stats.gerais.total_despesas) }}</h3>
              <p class="mb-0 small">Total Despesas</p>
            </div>
          </div>
        </div>
        <div class="col-6 col-lg-3">
          <div class="card text-center bg-info text-white h-100">
            <div class="card-body py-3">
              <h3 class="mb-1">{{ formatCurrencyShort(stats.gerais.media_despesas) }}</h3>
              <p class="mb-0 small">Média por Registro</p>
            </div>
          </div>
        </div>
        <div class="col-6 col-lg-3">
          <div class="card text-center bg-secondary text-white h-100">
            <div class="card-body py-3">
              <h3 class="mb-1">{{ stats.gerais.total_registros }}</h3>
              <p class="mb-0 small">Registros</p>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="col-lg-6 mb-4">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">Distribuição por UF</h5>
            </div>
            <div class="card-body" style="height: 300px;">
              <canvas ref="chartUf"></canvas>
            </div>
          </div>
        </div>

        <div class="col-lg-6 mb-4">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">Top 5 Operadoras</h5>
            </div>
            <div class="card-body" style="height: 300px;">
              <canvas ref="chartTop"></canvas>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="col-lg-6 mb-4">
          <div class="card" style="height: 420px;">
            <div class="card-header">
              <h5 class="mb-0">Despesas por UF</h5>
            </div>
            <div class="card-body p-0" style="overflow-y: auto; max-height: 360px;">
              <div class="table-responsive">
                <table class="table table-striped table-sm mb-0">
                  <thead>
                    <tr>
                      <th>UF</th>
                      <th class="text-end">Total</th>
                      <th class="text-end">Operadoras</th>
                      <th class="text-end">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="uf in stats.distribuicao_uf" :key="uf.uf">
                      <td>{{ uf.uf }}</td>
                      <td class="text-end">{{ formatCurrencyShort(uf.total_despesas) }}</td>
                      <td class="text-end">{{ uf.num_operadoras }}</td>
                      <td class="text-end">{{ uf.percentual }}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <div class="col-lg-6 mb-4">
          <div class="card" style="height: 420px;">
            <div class="card-header">
              <h5 class="mb-0">Top 5 Operadoras por Despesas</h5>
            </div>
            <div class="card-body p-0">
              <div class="table-responsive">
                <table class="table table-striped table-sm mb-0">
                  <thead>
                    <tr>
                      <th>Operadora</th>
                      <th>UF</th>
                      <th class="text-end">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(op, index) in stats.top_operadoras" :key="op.cnpj">
                      <td>
                        <span class="badge bg-primary me-2">{{ index + 1 }}</span>
                        <router-link :to="`/operadoras/${op.cnpj}`">
                          {{ truncate(op.razao_social, 30) }}
                        </router-link>
                      </td>
                      <td>{{ op.uf || '-' }}</td>
                      <td class="text-end">{{ formatCurrencyShort(op.total_despesas) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api.js'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'Estatisticas',
  data() {
    return {
      stats: null,
      loading: false,
      error: null,
      chartUfInstance: null,
      chartTopInstance: null
    }
  },
  methods: {
    async fetchEstatisticas() {
      this.loading = true
      this.error = null
      try {
        this.stats = await api.getEstatisticas()
        // Aguarda o DOM ser atualizado antes de renderizar os gráficos
        await this.$nextTick()
        setTimeout(() => this.renderCharts(), 100)
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    renderCharts() {
      this.renderUfChart()
      this.renderTopChart()
    },
    renderUfChart() {
      if (this.chartUfInstance) {
        this.chartUfInstance.destroy()
      }

      const ctx = this.$refs.chartUf
      if (!ctx || !this.stats) return

      const data = this.stats.distribuicao_uf.slice(0, 10)
      
      this.chartUfInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.map(d => d.uf),
          datasets: [{
            label: 'Total de Despesas (Bilhões R$)',
            data: data.map(d => parseFloat(d.total_despesas) / 1e9),
            backgroundColor: [
              '#0d6efd', '#198754', '#dc3545', '#ffc107', '#0dcaf0',
              '#6f42c1', '#fd7e14', '#20c997', '#6c757d', '#d63384'
            ]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              title: { display: true, text: 'Bilhões (R$)' }
            }
          }
        }
      })
    },
    renderTopChart() {
      if (this.chartTopInstance) {
        this.chartTopInstance.destroy()
      }

      const ctx = this.$refs.chartTop
      if (!ctx || !this.stats) return

      const data = this.stats.top_operadoras
      
      this.chartTopInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: data.map(d => this.truncate(d.razao_social, 20)),
          datasets: [{
            data: data.map(d => parseFloat(d.total_despesas)),
            backgroundColor: [
              '#0d6efd', '#198754', '#dc3545', '#ffc107', '#0dcaf0'
            ]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: { boxWidth: 12 }
            }
          }
        }
      })
    },
    formatCurrencyShort(value) {
      if (!value) return 'R$ 0'
      const num = parseFloat(value)
      if (num >= 1e9) return `R$ ${(num / 1e9).toFixed(2)} bi`
      if (num >= 1e6) return `R$ ${(num / 1e6).toFixed(2)} mi`
      if (num >= 1e3) return `R$ ${(num / 1e3).toFixed(2)} mil`
      return `R$ ${num.toFixed(2)}`
    },
    truncate(str, len) {
      if (!str) return ''
      return str.length > len ? str.substring(0, len) + '...' : str
    }
  },
  mounted() {
    this.fetchEstatisticas()
  },
  beforeUnmount() {
    if (this.chartUfInstance) this.chartUfInstance.destroy()
    if (this.chartTopInstance) this.chartTopInstance.destroy()
  }
}
</script>
