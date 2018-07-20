import * as React from 'react';
import * as _ from 'lodash';

import { BuildModel } from '../models/build';
import Logs from '../containers/logs';
import Statuses from '../containers/statuses';
import {
  isTrue,
  getBuildUrl,
  getProjectUrl,
  getUserUrl,
  splitUniqueName,
} from '../constants/utils';
import Breadcrumb from './breadcrumb';
import LinkedTab from './linkedTab';
import BuildOverview from './buildOverview';
import Text from './text';
import { EmptyList } from './empty/emptyList';
import BuildInstructions from './instructions/buildInstructions';
import { Bookmark } from '../constants/bookmarks';

export interface Props {
  build: BuildModel;
  onDelete: () => any;
  fetchData: () => any;
  bookmark: () => any;
  unbookmark: () => any;
}

export default class BuildDetail extends React.Component<Props, Object> {
  componentDidMount() {
    this.props.fetchData();
  }

  public render() {
    const build = this.props.build;
    if (_.isNil(build)) {
      return EmptyList(false, 'build', 'build');
    }

    const bookmark: Bookmark = {
      active: isTrue(this.props.build.bookmarked),
      callback: isTrue(this.props.build.bookmarked) ? this.props.unbookmark : this.props.bookmark
    };
    let values = splitUniqueName(build.project);
    let buildUrl = getBuildUrl(values[0], values[1], this.props.build.id);
    let projectUrl = getProjectUrl(values[0], values[1]);
    let breadcrumbLinks = [
      {name: values[0], value: getUserUrl(values[0])},
      {name: values[1], value: projectUrl},
      {name: 'Builds', value: `${projectUrl}#builds`},
      {name: `Build ${build.id}`}];
    return (
      <div className="row">
        <div className="col-md-12">
          <div className="entity-details">
            <Breadcrumb
              icon="fa-gavel"
              links={breadcrumbLinks}
              bookmark={bookmark}
            />
            <LinkedTab
              baseUrl={buildUrl}
              tabs={[
                {
                  title: 'Overview',
                  component: <BuildOverview build={build}/>,
                  relUrl: ''
                }, {
                  title: 'Logs',
                  component: <Logs
                    fetchData={() => null}
                    logs={''}
                    user={build.user}
                    project={build.project}
                    resource="builds"
                    id={build.id}
                  />,
                  relUrl: 'logs'
                }, {
                  title: 'Dockerfile',
                  component: <Text title="Dockerfile" text={build.dockerfile}/>,
                  relUrl: 'dockerfile'
                }, {
                  title: 'Statuses',
                  component: <Statuses
                    project={build.project}
                    resource="builds"
                    id={build.id}
                  />,
                  relUrl: 'statuses'
                }, {
                  title: 'Instructions',
                  component: <BuildInstructions id={build.id}/>,
                  relUrl: 'instructions'
                }
              ]}
            />
          </div>
        </div>
      </div>
    );
  }
}
