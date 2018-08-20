import { LastFetchedIds } from './utils';

export class StatusModel {
  public id: number;
  public uuid: string;
  public created_at: string;
  public status: string;
  public message: string;
  public details: Object;
}

export class StatusStateSchema {
  public byIds: {[id: number]: StatusModel};
  public ids: number[];
  public lastFetched: LastFetchedIds;
}

export const StatusEmptyState = {
  byIds: {},
  ids: [],
  lastFetched: new LastFetchedIds()
};
