import rawData from '../data/characters.json';
import type { Band, CharacterData } from '../types';

const data = rawData as CharacterData;

const BAND_BY_ID = new Map<string, Band>(data.bands.map((band) => [band.id, band]));

export function bandOf(bandId: string): Band | undefined {
  return BAND_BY_ID.get(bandId);
}
