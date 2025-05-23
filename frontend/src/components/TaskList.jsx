import React from 'react';
import { Droppable } from '@hello-pangea/dnd';
import { PlusIcon } from '@radix-ui/react-icons';
import TaskItem from './TaskItem';

const TaskList = ({
  tasks,
  parentId,
  parentType,
  editingTask,
  editInputBottomRef,
  handleTaskClick,
  handleCompleteTask,
  handleDeleteTask,
  handleSecondaryTask,
  handleTaskChange,
  handleTaskBlur,
  handleTaskKeyPress,
  handleAddTask,
  className = ''
}) => (
  <Droppable droppableId={`${parentId}-${parentType}`} type="task">
    {(provided) => (
      <div
        {...provided.droppableProps}
        ref={provided.innerRef}
        className={className}
      >
        {tasks.map((task, index) => (
          <TaskItem
            key={`task-${task.key}`}
            task={task}
            index={index}
            editing={editingTask?.key === task.key}
            editingTask={editingTask}
            onEdit={handleTaskClick}
            onComplete={handleCompleteTask}
            onDelete={handleDeleteTask}
            onSecondary={handleSecondaryTask}
            inputRef={editInputBottomRef}
            onChange={handleTaskChange}
            onBlur={() => handleTaskBlur(task)}
            onKeyDown={handleTaskKeyPress}
          />
        ))}
        {provided.placeholder}
        <div className="group flex items-center">
          <PlusIcon
            className="invisible group-hover:visible cursor-pointer text-gray-400 hover:text-black add-button h-3 w-3"
            onClick={() => handleAddTask(parentId, parentType)}
          />
        </div>
      </div>
    )}
  </Droppable>
);

export default TaskList;
