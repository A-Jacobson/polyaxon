import * as React from 'react';
import { LinkContainer } from 'react-router-bootstrap';

import {
  getGroupUrl,
  splitUniqueName
} from '../constants/utils';
import { GroupModel } from '../models/group';
import Description from './description';
import ConcurrencyMetaInfo from './metaInfo/concurrencyMetaInfo';
import DatesMetaInfo from './metaInfo/datesMetaInfo';
import SearchAlgorithmMetaInfo from './metaInfo/searchAlgorithmMetaInfo';
import TaskRunMetaInfo from './metaInfo/taskRunMetaInfo';
import UserMetaInfo from './metaInfo/userMetaInfo';
import Status from './status';
import Tags from './tags';

export interface Props {
  group: GroupModel;
  onDelete: () => void;
}

function Group({group, onDelete}: Props) {
  const values = splitUniqueName(group.project);
  return (
    <div className="row">
      <div className="col-md-1 block">
        <Status status={group.last_status}/>
      </div>
      <div className="col-md-7 block">
        <LinkContainer to={getGroupUrl(values[0], values[1], group.id)}>
          <a className="title">
            <i className="fa fa-cubes icon" aria-hidden="true"/>
            {group.unique_name}
          </a>
        </LinkContainer>
        <Description description={group.description}/>
        <div className="meta">
          <UserMetaInfo user={group.user} inline={true}/>
          <DatesMetaInfo
            createdAt={group.created_at}
            updatedAt={group.updated_at}
            inline={true}
          />
        </div>
        <Tags tags={group.tags}/>
      </div>
      <div className="col-md-2 block">
        <SearchAlgorithmMetaInfo searchAlgorithm={group.search_algorithm}/>
        <ConcurrencyMetaInfo concurrency={group.concurrency}/>
      </div>
      <div className="col-md-2 block">
        <TaskRunMetaInfo startedAt={group.started_at} finishedAt={group.finished_at}/>
      </div>
    </div>
  );
}

export default Group;
