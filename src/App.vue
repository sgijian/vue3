<script setup lang="ts">

</script>

<template>
  <div class="app-container">
    <!-- 根组件仅作为路由视图的容器 -->
    <router-view />
  </div>
</template>

<style scoped>
.app-container {
  /* 保持基础样式，具体页面样式在各 View 组件中定义 */
  min-height: 100vh;
  background-color: #f5f7fa;
}
</style>