import React from 'react';
import TaskList from './TaskList';

const ObjectiveList = ({
  area,
  objectives,
  tasks,
  editingTask,
  editInputBottomRef,
  handleTaskClick,
  handleCompleteTask,
  handleDeleteTask,
  handleSecondaryTask,
  handleTaskChange,
  handleTaskBlur,
  handleTaskKeyPress,
  handleAddTask
}) => (
  <div className="pl-4 space-y-1">
  {objectives
      .filter(obj => obj.area_key === area.key)
      .sort((a, b) => a.order_index - b.order_index)
      .map((objective, index) => {
        const objectiveTasks = tasks
          .filter(task => task.objective_key === objective.key)
          .sort((a, b) => a.order_index - b.order_index);
        return (
        <div key={`bottom-${objective.key}`} className="group">
          <div className="flex items-center italic">
            <span className={objective.status === 'complete' ? 'line-through' : ''}>
              {index + 1}. {objective.text}{objectiveTasks.length > 0 && ' •'}
            </span>
          </div>
          <TaskList
            tasks={objectiveTasks}
            parentId={objective.key}
            parentType="objective"
            editingTask={editingTask}
            editInputBottomRef={editInputBottomRef}
            handleTaskClick={handleTaskClick}
            handleCompleteTask={handleCompleteTask}
            handleDeleteTask={handleDeleteTask}
            handleSecondaryTask={handleSecondaryTask}
            handleTaskChange={handleTaskChange}
            handleTaskBlur={handleTaskBlur}
            handleTaskKeyPress={handleTaskKeyPress}
            handleAddTask={handleAddTask}
            className="pl-5 space-y-1 mt-1 mb-4"
          />
        </div>
      )})}
  </div>
);

export default ObjectiveList;
