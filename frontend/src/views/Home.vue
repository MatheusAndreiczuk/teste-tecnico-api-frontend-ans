<template>
  <div class="py-3">
    <div class="text-center mb-4">
      <h1 class="h2">Sistema ANS</h1>
      <p class="text-muted">
        Consulta de operadoras de planos de saúde e análise de despesas
      </p>
    </div>

    <div class="row g-3">
      <div class="col-sm-6">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">Operadoras</h5>
            <p class="card-text small">
              Lista de operadoras ativas com busca por nome, CNPJ e filtro por estado.
            </p>
            <router-link to="/operadoras" class="btn btn-primary btn-sm">
              Ver Operadoras
            </router-link>
          </div>
        </div>
      </div>
      
      <div class="col-sm-6">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">Estatísticas</h5>
            <p class="card-text small">
              Visão geral das despesas, distribuição por UF e ranking das maiores operadoras.
            </p>
            <router-link to="/estatisticas" class="btn btn-primary btn-sm">
              Ver Estatísticas
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <div class="card bg-light mt-3">
      <div class="card-body py-2">
        <h6 class="card-title mb-1">Sobre os dados</h6>
        <p class="card-text small mb-0">
          Dados públicos da Agência Nacional de Saúde Suplementar (ANS), 
          referentes aos últimos 3 trimestres disponíveis.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HomeView'
}
</script>
