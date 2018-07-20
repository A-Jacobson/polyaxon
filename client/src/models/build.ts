import { LastFetchedNames } from './utils';

export class BuildModel {
  public id: number;
  public uuid: string;
  public unique_name: string;
  public name: string;
  public user: string;
  public definition: string;
  public description: string;
  public deleted?: boolean;
  public project: string;
  public tags: Array<string> = [];
  public last_status: string;
  public created_at: string;
  public updated_at: string;
  public started_at: string;
  public finished_at: string;
  public commit: string;
  public dockerfile: string;
  public resources: {[key: string]: any};
  public bookmarked: boolean;
}

export class BuildStateSchema {
  byUniqueNames: {[uniqueName: string]: BuildModel};
  uniqueNames: string[];
  lastFetched: LastFetchedNames;
}

export const BuildsEmptyState = {
  byUniqueNames: {},
  uniqueNames: [],
  lastFetched: new LastFetchedNames()
};
