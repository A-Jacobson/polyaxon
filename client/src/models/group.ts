import { LastFetchedNames } from './utils';

export class GroupModel {
  public uuid: string;
  public unique_name: string;
  public description: string;
  public id: number;
  public num_experiments: number;
  public user: string;
  public concurrency: number;
  public content: string;
  public tags: string[] = [];
  public num_scheduled_experiments: number;
  public num_pending_experiments: number;
  public num_running_experiments: number;
  public num_succeeded_experiments: number;
  public num_failed_experiments: number;
  public num_stopped_experiments: number;
  public deleted?: boolean;
  public created_at: string;
  public updated_at: string;
  public started_at: string;
  public finished_at: string;
  public last_status: string;
  public current_iteration: number;
  public search_algorithm: string;
  public project: string;
  public has_tensorboard: boolean;
  public experiments: string[] = [];
  public bookmarked: boolean;
}

export class GroupStateSchema {
  public byUniqueNames: { [uniqueName: string]: GroupModel };
  public uniqueNames: string[];
  public lastFetched: LastFetchedNames;
}

export const GroupsEmptyState = {
  byUniqueNames: {},
  uniqueNames: [],
  lastFetched: new LastFetchedNames()
};
