import { tracks } from '../.vitepress/theme/data/tracks'

export default {
  paths: () =>
    tracks.map((track) => ({
      params: {
        track: track.slug,
        title: `Track ${track.num} — ${track.title.en}`,
        description: track.summary.en,
      },
    })),
}
