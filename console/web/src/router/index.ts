import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Layout from '../views/Layout.vue'
import Dashboard from '../views/Dashboard.vue'
import ReviewStation from '../views/ReviewStation.vue'
import AssetManager from '../views/AssetManager.vue'
import SkillEditor from '../views/SkillEditor.vue'
import UserRoles from '../views/UserRoles.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login },
    {
      path: '/',
      component: Layout,
      children: [
        { path: '', component: Dashboard },
        { path: 'reviews', component: ReviewStation },
        { path: 'assets', component: AssetManager },
        { path: 'assets/:agentName/skills/:skillName', component: SkillEditor, props: true },
        { path: 'assets/:agentName/rag/:docName', component: SkillEditor, props: true },
        { path: 'assets/:agentName/skills-new', component: SkillEditor, props: true },
        { path: 'assets/:agentName/rag-new', component: SkillEditor, props: true },
        { path: 'users', component: UserRoles },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
