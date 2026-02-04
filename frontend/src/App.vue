<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
      <div class="container">
        <router-link class="navbar-brand" to="/">ANS Operadoras</router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <div class="navbar-nav">
            <router-link class="nav-link" to="/">Home</router-link>
            <router-link class="nav-link" to="/operadoras">Operadoras</router-link>
            <router-link class="nav-link" to="/estatisticas">Estatísticas</router-link>
          </div>
        </div>
      </div>
    </nav>
    <main class="container pb-5">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
body {
  background-color: #f5f5f5;
  min-height: 100vh;
}
.navbar-brand {
  font-weight: bold;
}
@media (max-width: 768px) {
  .table-responsive {
    font-size: 0.85rem;
  }
}
</style>
