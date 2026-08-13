import type { Theme } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import './custom.css'

import HomePage from './components/HomePage.vue'
import PageHeader from './components/PageHeader.vue'
import SectionHead from './components/SectionHead.vue'
import AgentFlow from './components/AgentFlow.vue'
import TrackExplorer from './components/TrackExplorer.vue'
import TrackPath from './components/TrackPath.vue'
import TrackDetail from './components/TrackDetail.vue'
import PatternGrid from './components/PatternGrid.vue'
import CookbookGrid from './components/CookbookGrid.vue'
import DemoGrid from './components/DemoGrid.vue'
import BenchTable from './components/BenchTable.vue'
import BenchNotes from './components/BenchNotes.vue'
import MetaBadges from './components/MetaBadges.vue'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('HomePage', HomePage)
    app.component('PageHeader', PageHeader)
    app.component('SectionHead', SectionHead)
    app.component('AgentFlow', AgentFlow)
    app.component('TrackExplorer', TrackExplorer)
    app.component('TrackPath', TrackPath)
    app.component('TrackDetail', TrackDetail)
    app.component('PatternGrid', PatternGrid)
    app.component('CookbookGrid', CookbookGrid)
    app.component('DemoGrid', DemoGrid)
    app.component('BenchTable', BenchTable)
    app.component('BenchNotes', BenchNotes)
    app.component('MetaBadges', MetaBadges)
  },
} satisfies Theme
