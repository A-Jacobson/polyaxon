import * as React from 'react';
import './instructions.less';

export interface Props {
  projectName: string;
}

function ProjectInstructions({projectName}: Props) {
  return (
    <div className="instructions">
      <div className="row">
        <div className="col-md-12">
          <div className="instructions-header">
            Instructions
          </div>
        </div>
      </div>
      <div className="row">
        <div className="col-md-12">
          <div className="instructions-content">
            <div className="instructions-section">
              <h4>Filters</h4>
              <ul>
                <li>
                  <a href="https://docs.polyaxon.com/query_syntax/introduction/">
                    Understanding the query syntax
                  </a>
                </li>
                <li>
                  <a href="https://docs.polyaxon.com/query_syntax/entities/jobs/">
                    Searching Jobs
                  </a>
                </li>
                <li>
                  <a href="https://docs.polyaxon.com/query_syntax/entities/experiments/">
                    Searching Experiments
                  </a>
                </li>
                <li>
                  <a href="https://docs.polyaxon.com/query_syntax/entities/experiment_groups/">
                    Searching Groups
                  </a>
                </li>
              </ul>
            </div>
            <div className="instructions-section">
              <h4>Init project</h4>
              <div className="instructions-section-content">
                polyaxon init {projectName}
              </div>
            </div>
            <div className="instructions-section">
              <h4>Add/update the project's description</h4>
              <div className="instructions-section-content">
                polyaxon project update --description="My new description for the project..."
              </div>
            </div>
            <div className="instructions-section">
              <h4>Add/update the project's tags</h4>
              <div className="instructions-section-content">
                polyaxon project update --tags="foo, bar, ..,"
              </div>
            </div>
            <div className="instructions-section">
              <h4>Start experiment/experiment group/job/build</h4>
              <div className="instructions-section-content">
                polyaxon run -f polyaxonfile.yml [-f override_file.yml] [-u] [--name] [--description] [--tags]
              </div>
            </div>
            <div className="instructions-section">
              <h4>Start a notebook</h4>
              <div className="instructions-section-content">
                polyaxon notebook start -f polyaxonfile.yml [-f override_file.yml] [-u]
              </div>
            </div>
            <div className="instructions-section">
              <h4>Start a tensorboard</h4>
              <div className="instructions-section-content">
                polyaxon tensorboard start [-f polyaxonfile.yml] [-f override_file.yml] [-u]
              </div>
            </div>
             <div className="instructions-section">
              <h4>Bookmark project</h4>
              <div className="instructions-section-content">
                polyaxon project bookmark
              </div>
              <div className="instructions-section-content">
                polyaxon project unbookmark
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProjectInstructions;
