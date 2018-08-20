import * as _ from 'lodash';
import * as React from 'react';

import { JobModel } from '../models/job';
import { EmptyList } from './empty/emptyList';

export interface Props {
  job: JobModel;
  onDelete: () => any;
  fetchData: () => any;
}

export default class JobDetail extends React.Component<Props, Object> {
  public componentDidMount() {
    this.props.fetchData();
  }

  public render() {
    const job = this.props.job;
    if (_.isNil(job)) {
      return EmptyList(false, 'experiment', 'experiment');
    }
    return (
      <div className="row">
        <div className="col-md-12">
          <div className="entity-details">
            <a className="back-button" onClick={() => {window.history.back(); }}>&#060;</a>
            <span className="title">
              <i className="fa fa-cube icon" aria-hidden="true"/>
              {job.unique_name}
            </span>
            <span className="description">
              <pre>{JSON.stringify(job.definition, null, 2)}</pre>
            </span>
          </div>
        </div>
      </div>
    );
  }
}
