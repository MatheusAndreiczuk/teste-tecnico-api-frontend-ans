<template>
  <div class="pb-4">
    <div class="mb-3">
      <button @click="$router.back()" class="btn btn-outline-secondary btn-sm">
        ← Voltar
      </button>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Carregando...</span>
      </div>
    </div>

    <div v-else-if="error" class="alert alert-danger">
      <strong>Erro:</strong> {{ error }}
      <button class="btn btn-sm btn-outline-danger ms-3" @click="fetchOperadora">
        Tentar novamente
      </button>
    </div>

    <div v-else-if="operadora">
      <div class="card mb-3">
        <div class="card-header bg-primary text-white py-2">
          <h5 class="mb-0">{{ operadora.razao_social || 'Operadora' }}</h5>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-sm-6 mb-2 mb-sm-0">
              <p class="mb-1"><strong>CNPJ:</strong> {{ formatCnpj(operadora.cnpj) }}</p>
              <p class="mb-1"><strong>Registro ANS:</strong> {{ operadora.registro_ans || '-' }}</p>
              <p class="mb-0"><strong>Modalidade:</strong> {{ operadora.modalidade || '-' }}</p>
            </div>
            <div class="col-sm-6">
              <p class="mb-1"><strong>UF:</strong> {{ operadora.uf || '-' }}</p>
              <p class="mb-1"><strong>Total Despesas:</strong> {{ formatCurrency(operadora.total_despesas) }}</p>
              <p class="mb-0"><strong>Trimestres:</strong> {{ operadora.num_trimestres || 0 }}</p>
            </div>
          </div>
        </div>
      </div>

      <h6 class="mb-2">Histórico de Despesas</h6>

      <div v-if="loadingDespesas" class="text-center py-3">
        <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
        <span class="ms-2">Carregando despesas...</span>
      </div>

      <div v-else-if="despesas.length === 0" class="alert alert-info">
        Nenhuma despesa registrada para esta operadora.
      </div>

      <div v-else>
        <div class="table-responsive">
          <table class="table table-striped table-sm bg-white">
            <thead class="table-dark">
              <tr>
                <th>Trimestre</th>
                <th>Ano</th>
                <th class="text-end">Valor</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in despesas" :key="`${d.ano}-${d.trimestre}`">
                <td>{{ d.trimestre }}</td>
                <td>{{ d.ano }}</td>
                <td class="text-end">{{ formatCurrency(d.valor_despesas) }}</td>
              </tr>
            </tbody>
            <tfoot class="table-secondary">
              <tr>
                <th colspan="2">Total</th>
                <th class="text-end">{{ formatCurrency(totalDespesas) }}</th>
              </tr>
            </tfoot>
          </table>
        </div>

        <nav v-if="despesasPages > 1">
          <ul class="pagination pagination-sm justify-content-center">
            <li class="page-item" :class="{ disabled: despesasPage === 1 }">
              <button class="page-link" @click="goToDespesasPage(despesasPage - 1)">Anterior</button>
            </li>
            <li class="page-item" :class="{ active: despesasPage === p }" v-for="p in despesasPages" :key="p">
              <button class="page-link" @click="goToDespesasPage(p)">{{ p }}</button>
            </li>
            <li class="page-item" :class="{ disabled: despesasPage === despesasPages }">
              <button class="page-link" @click="goToDespesasPage(despesasPage + 1)">Próximo</button>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api.js'

export default {
  name: 'OperadoraDetalhe',
  data() {
    return {
      operadora: null,
      despesas: [],
      loading: false,
      loadingDespesas: false,
      error: null,
      despesasPage: 1,
      despesasPages: 1
    }
  },
  computed: {
    cnpj() {
      return this.$route.params.cnpj
    },
    totalDespesas() {
      return this.despesas.reduce((sum, d) => sum + parseFloat(d.valor_despesas || 0), 0)
    }
  },
  methods: {
    async fetchOperadora() {
      this.loading = true
      this.error = null
      try {
        this.operadora = await api.getOperadora(this.cnpj)
        await this.fetchDespesas()
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async fetchDespesas() {
      this.loadingDespesas = true
      try {
        const response = await api.getDespesasOperadora(this.cnpj, {
          page: this.despesasPage,
          limit: 10
        })
        this.despesas = response.data
        this.despesasPages = response.pages
      } catch (err) {
        console.error('Erro ao carregar despesas:', err)
      } finally {
        this.loadingDespesas = false
      }
    },
    goToDespesasPage(p) {
      if (p >= 1 && p <= this.despesasPages) {
        this.despesasPage = p
        this.fetchDespesas()
      }
    },
    formatCnpj(cnpj) {
      if (!cnpj || cnpj.length !== 14) return cnpj
      return cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5')
    },
    formatCurrency(value) {
      if (!value) return 'R$ 0,00'
      return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
      }).format(value)
    }
  },
  mounted() {
    this.fetchOperadora()
  },
  watch: {
    cnpj() {
      this.fetchOperadora()
    }
  }
}
</script>
