import type { Pinia } from 'pinia'
import { createRouter, createWebHistory, type RouterHistory } from 'vue-router'

import LoginPage from '../features/auth/LoginPage.vue'
import AssessmentCenterPage from '../features/assessment/AssessmentCenterPage.vue'
import AssessmentReportPage from '../features/assessment/AssessmentReportPage.vue'
import AssessmentRunnerPage from '../features/assessment/AssessmentRunnerPage.vue'
import DashboardPage from '../features/profile/DashboardPage.vue'
import PrivacyPage from '../features/profile/PrivacyPage.vue'
import ProfilePage from '../features/profile/ProfilePage.vue'
import CompetencyPage from '../features/competency/CompetencyPage.vue'
import TargetExplorerPage from '../features/targets/TargetExplorerPage.vue'
import PlanningPage from '../features/planning/PlanningPage.vue'
import PlanHistoryPage from '../features/planning/PlanHistoryPage.vue'
import TaskBoardPage from '../features/tasks/TaskBoardPage.vue'
import WeeklyReportsPage from '../features/reports/WeeklyReportsPage.vue'
import MentorStudentsPage from '../features/mentor/MentorStudentsPage.vue'
import AdminOverviewPage from '../features/admin/AdminOverviewPage.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import MentorLayout from '../layouts/MentorLayout.vue'
import StudentLayout from '../layouts/StudentLayout.vue'
import { useSessionStore, type UserRole } from './session'

const placeholder = (title: string) => ({ template: `<section><h2>${title}</h2></section>` })

export function createCareerRouter(history: RouterHistory = createWebHistory(), pinia?: Pinia) {
  const router = createRouter({
    history,
    routes: [
      { path: '/login', name: 'login', component: LoginPage, meta: { public: true } },
      { path: '/forbidden', name: 'forbidden', component: placeholder('无权访问'), meta: { public: true } },
      {
        path: '/',
        component: StudentLayout,
        meta: { roles: ['student'] },
        children: [
          { path: '', name: 'dashboard', component: DashboardPage },
          { path: 'profile', component: ProfilePage },
          { path: 'privacy', component: PrivacyPage },
          { path: 'assessments', component: AssessmentCenterPage },
          { path: 'assessments/:scaleId', component: AssessmentRunnerPage, props: true },
          { path: 'assessment-reports/:recordId', component: AssessmentReportPage, props: true },
          { path: 'competencies', component: CompetencyPage },
          { path: 'targets', component: TargetExplorerPage },
          { path: 'planning', component: PlanningPage },
          { path: 'plans/history', component: PlanHistoryPage },
          { path: 'tasks', component: TaskBoardPage },
          { path: 'reports', component: WeeklyReportsPage },
        ],
      },
      { path: '/mentor', component: MentorLayout, meta: { roles: ['mentor'] }, children: [{ path: '', component: MentorStudentsPage }] },
      { path: '/admin', component: AdminLayout, meta: { roles: ['admin'] }, children: [{ path: '', name: 'admin', component: AdminOverviewPage }] },
    ],
  })
  router.beforeEach((to) => {
    const session = useSessionStore(pinia)
    if (to.meta.public) return true
    if (!session.authenticated) return { name: 'login' }
    const roles = to.meta.roles as UserRole[] | undefined
    if (roles && (!session.role || !roles.includes(session.role))) return { name: 'forbidden' }
    return true
  })
  return router
}
