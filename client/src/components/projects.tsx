import * as React from 'react';
import * as _ from 'lodash';

import Project from './project';
import { ProjectModel } from '../models/project';
import PaginatedList from '../components/paginatedList';
import { EmptyList } from './emptyList';
import ProjectHeader from './projectHeader';

export interface Props {
  isCurrentUser: boolean;
  user: string;
  projects: ProjectModel[];
  count: number;
  onUpdate: (project: ProjectModel) => any;
  onDelete: (project: ProjectModel) => any;
  fetchData: () => any;
}

export default class Projects extends React.Component<Props, Object> {
  public render() {
    const projects = this.props.projects;
    const listProjects = () => {
        return (
          <ul>
            {projects.filter(
              (project: ProjectModel) => _.isNil(project.deleted) || !project.deleted
            ).map(
              (project: ProjectModel) => <li className="list-item" key={project.unique_name}>
                <Project project={project} onDelete={() => this.props.onDelete(project)}/></li>)}
          </ul>
        );
      }
    ;

    return (
      <PaginatedList
        count={this.props.count}
        componentList={listProjects()}
        componentHeader={ProjectHeader()}
        componentEmpty={EmptyList(
          this.props.isCurrentUser,
          'project',
          'project',
          'polyaxon project create --help')}
        filters={false}
        fetchData={this.props.fetchData}
      />
    );
  }
}
