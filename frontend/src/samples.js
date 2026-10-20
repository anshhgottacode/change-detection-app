const base = import.meta.env.BASE_URL

export const SAMPLES = [
  {
    id: 'objects',
    title: 'Objects added',
    desc: 'Fixed camera, new objects on the desk',
    before: `${base}samples/objects_before.jpg`,
    after: `${base}samples/objects_after.jpg`,
    settings: {},
  },
  {
    id: 'shift',
    title: 'Camera moved',
    desc: 'Same scene from a shifted position',
    before: `${base}samples/shift_before.jpg`,
    after: `${base}samples/shift_after.jpg`,
    settings: { align: true },
  },
  {
    id: 'light',
    title: 'Lighting changed',
    desc: 'Same scene, different lighting',
    before: `${base}samples/light_before.jpg`,
    after: `${base}samples/light_after.jpg`,
    settings: { normalize: 'clahe' },
  },
]