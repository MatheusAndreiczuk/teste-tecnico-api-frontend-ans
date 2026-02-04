<template>
  <div>
    <h2 class="mb-3">Operadoras</h2>

    <div class="card mb-3">
      <div class="card-body py-2">
        <div class="row g-2">
          <div class="col-12 col-md-6">
            <input
              type="text"
              class="form-control form-control-sm"
              placeholder="Buscar por razão social ou CNPJ..."
              v-model="searchTerm"
              @input="onSearchDebounced"
            >
          </div>
          <div class="col-6 col-md-3">
            <select class="form-select form-select-sm" v-model="selectedUf" @change="fetchOperadoras">
              <option value="">Todos UFs</option>
              <option v-for="uf in ufs" :key="uf" :value="uf">{{ uf }}</option>
            </select>
          </div>
          <div class="col-6 col-md-3">
            <select class="form-select form-select-sm" v-model="limit" @change="fetchOperadoras">
              <option :value="10">10 por pág</option>
              <option :value="25">25 por pág</option>
              <option :value="50">50 por pág</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Carregando...</span>
      </div>
      <p class="mt-2">Carregando operadoras...</p>
    </div>

    <div v-else-if="error" class="alert alert-danger">
      <strong>Erro:</strong> {{ error }}
      <button class="btn btn-sm btn-outline-danger ms-3" @click="fetchOperadoras">
        Tentar novamente
      </button>
    </div>

    <div v-else-if="operadoras.length === 0" class="alert alert-info">
      Nenhuma operadora encontrada com os filtros aplicados.
    </div>

    <div v-else class="mb-4">
      <div class="table-responsive">
        <table class="table table-striped table-hover bg-white table-sm">
          <thead class="table-dark">
            <tr>
              <th class="d-none d-md-table-cell">CNPJ</th>
              <th>Razão Social</th>
              <th class="d-none d-lg-table-cell">Registro ANS</th>
              <th class="d-none d-xl-table-cell">Modalidade</th>
              <th>UF</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="op in operadoras" :key="op.cnpj">
              <td class="d-none d-md-table-cell">{{ formatCnpj(op.cnpj) }}</td>
              <td>{{ op.razao_social || '-' }}</td>
              <td class="d-none d-lg-table-cell">{{ op.registro_ans || '-' }}</td>
              <td class="d-none d-xl-table-cell">{{ op.modalidade || '-' }}</td>
              <td>{{ op.uf || '-' }}</td>
              <td>
                <router-link 
                  :to="`/operadoras/${op.cnpj}`" 
                  class="btn btn-sm btn-primary"
                >
                  Ver
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <nav aria-label="Paginação" class="mt-3">
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-center gap-2">
          <span class="text-muted small">
            Mostrando {{ (page - 1) * limit + 1 }} - {{ Math.min(page * limit, total) }} de {{ total }} operadoras
          </span>
          <ul class="pagination pagination-sm mb-0">
            <li class="page-item" :class="{ disabled: page === 1 }">
              <button class="page-link" @click="goToPage(page - 1)">Anterior</button>
            </li>
            <li 
              v-for="p in visiblePages" 
              :key="p" 
              class="page-item" 
              :class="{ active: p === page }"
            >
              <button class="page-link" @click="goToPage(p)">{{ p }}</button>
            </li>
            <li class="page-item" :class="{ disabled: page === pages }">
              <button class="page-link" @click="goToPage(page + 1)">Próximo</button>
            </li>
          </ul>
        </div>
      </nav>
    </div>
  </div>
</template>

<script>
import api from '../services/api.js'

export default {
  name: 'Operadoras',
  data() {
    return {
      operadoras: [],
      loading: false,
      error: null,
      searchTerm: '',
      selectedUf: '',
      page: 1,
      limit: 10,
      total: 0,
      pages: 1,
      searchTimeout: null,
      ufs: ['AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT','PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO']
    }
  },
  computed: {
    visiblePages() {
      const range = []
      const start = Math.max(1, this.page - 2)
      const end = Math.min(this.pages, this.page + 2)
      for (let i = start; i <= end; i++) {
        range.push(i)
      }
      return range
    }
  },
  methods: {
    async fetchOperadoras() {
      this.loading = true
      this.error = null
      try {
        const params = {
          page: this.page,
          limit: this.limit
        }
        if (this.searchTerm) params.search = this.searchTerm
        if (this.selectedUf) params.uf = this.selectedUf

        const response = await api.getOperadoras(params)
        this.operadoras = response.data
        this.total = response.total
        this.pages = response.pages
      } catch (err) {
        this.error = err.message
        this.operadoras = []
      } finally {
        this.loading = false
      }
    },
    onSearchDebounced() {
      clearTimeout(this.searchTimeout)
      this.searchTimeout = setTimeout(() => {
        this.page = 1
        this.fetchOperadoras()
      }, 300)
    },
    goToPage(p) {
      if (p >= 1 && p <= this.pages) {
        this.page = p
        this.fetchOperadoras()
      }
    },
    formatCnpj(cnpj) {
      if (!cnpj || cnpj.length !== 14) return cnpj
      return cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5')
    }
  },
  mounted() {
    this.fetchOperadoras()
  }
}
</script>
