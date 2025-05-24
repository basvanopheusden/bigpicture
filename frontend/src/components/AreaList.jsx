import React from 'react';
import { Droppable, Draggable } from '@hello-pangea/dnd';
import { ChevronDownIcon, ChevronRightIcon, Cross2Icon, PlusIcon, CheckIcon } from '@radix-ui/react-icons';
import ReactMarkdown from 'react-markdown';
import TaskList from './TaskList';

const AreaList = ({
  areas,
  objectives,
  tasks,
  collapsedAreas,
  editingArea,
  editingObjective,
  editingTask,
  editInputRef,
  editInputBottomRef,
  handleAreaClick,
  toggleAreaCollapse,
  handleAreaChange,
  handleAreaBlur,
  handleAreaKeyPress,
  handleDeleteArea,
  handleAddArea,
  handleObjectiveClick,
  handleObjectiveChange,
  handleObjectiveBlur,
  handleObjectiveKeyPress,
  handleCompleteObjective,
  handleDeleteObjective,
  handleAddObjective,
  handleTaskClick,
  handleCompleteTask,
  handleDeleteTask,
  handleSecondaryTask,
  handleTaskChange,
  handleTaskBlur,
  handleTaskKeyPress,
  handleAddTask
}) => (
  <div className="flex-1 border-b p-4 sm:p-8 mx-2 sm:mx-32 max-w-[1200px] sm:max-w-none mt-4">
    <Droppable droppableId="areas-list-top" type="area">
      {(provided) => (
        <div
          {...provided.droppableProps}
          ref={provided.innerRef}
          className="space-y-4"
        >
          {areas.map((area, index) => (
            <Draggable key={area.key} draggableId={area.key} index={index}>
              {(provided, snapshot) => (
                <div
                  ref={provided.innerRef}
                  {...provided.draggableProps}
                  {...provided.dragHandleProps}
                  className={`${snapshot.isDragging ? 'opacity-50' : ''}`}
                >
                  <div
                    className="group flex items-center mb-2"
                    onClick={(e) => handleAreaClick(area, e)}
                  >
                    <button
                      onClick={(e) => { e.stopPropagation(); toggleAreaCollapse(area.key); }}
                      className="mr-2"
                    >
                      {collapsedAreas.has(area.key) ? <ChevronRightIcon /> : <ChevronDownIcon />}
                    </button>
                    <div className="flex-grow flex items-center">
                      {editingArea?.key === area.key ? (
                        <input
                          ref={editInputRef}
                          value={editingArea.text}
                          onChange={handleAreaChange}
                          onBlur={handleAreaBlur}
                          onKeyDown={handleAreaKeyPress}
                          className="font-extrabold outline-none font-mate text-sm bg-transparent"
                        />
                      ) : (
                        <>
                          <ReactMarkdown
                            className="font-extrabold"
                            components={{ p: ({node, ...props}) => <span {...props} /> }}
                          >
                            {area.text || '_'}
                          </ReactMarkdown>
                          <Cross2Icon
                            className="invisible group-hover:visible cursor-pointer ml-4 text-gray-400 hover:text-black delete-button h-3 w-3"
                            onClick={(e) => handleDeleteArea(area.key, e)}
                          />
                        </>
                      )}
                    </div>
                  </div>
                  {!collapsedAreas.has(area.key) && (
                    <>
                      <Droppable droppableId={area.key} type="objective">
                        {(provided) => (
                          <div
                            {...provided.droppableProps}
                            ref={provided.innerRef}
                            className="pl-4 space-y-1"
                          >
                          {objectives
                            .filter(obj => obj.area_key === area.key)
                            .sort((a, b) => a.order_index - b.order_index)
                            .map((objective, index) => (
                              <Draggable
                                key={objective.key}
                                draggableId={objective.key}
                                index={index}
                              >
                                {(provided, snapshot) => (
                                  <div
                                    ref={provided.innerRef}
                                    {...provided.draggableProps}
                                    className={`${snapshot.isDragging ? 'opacity-50' : ''}`}
                                  >
                                    <div
                                      {...provided.dragHandleProps}
                                      className="group flex items-center"
                                      onClick={(e) => handleObjectiveClick(objective, e)}
                                    >
                                      <div className="flex-grow flex items-center">
                                        {editingObjective?.key === objective.key ? (
                                          <input
                                            ref={editInputRef}
                                            value={editingObjective.text}
                                            onChange={handleObjectiveChange}
                                            onBlur={handleObjectiveBlur}
                                            onKeyDown={handleObjectiveKeyPress}
                                            className="outline-none font-mate text-sm bg-transparent w-full"
                                          />
                                        ) : (
                                          <>
                                            <span className={`italic ${objective.status === 'complete' ? 'line-through' : ''}`}>
                                              {index + 1}. <ReactMarkdown className="inline" components={{ p: ({node, ...props}) => <span {...props} /> }}>
                                                {objective.text || '_'}
                                              </ReactMarkdown>
                                            </span>
                                            <div className="invisible group-hover:visible flex items-center ml-4">
                                              <CheckIcon
                                                className="cursor-pointer text-gray-400 hover:text-black h-3 w-3 mr-2"
                                                onClick={(e) => handleCompleteObjective(objective, e)}
                                              />
                                              <Cross2Icon
                                                className="cursor-pointer text-gray-400 hover:text-black delete-button h-3 w-3"
                                                onClick={(e) => handleDeleteObjective(objective.key, e)}
                                              />
                                            </div>
                                          </>
                                        )}
                                      </div>
                                    </div>
                                    <TaskList
                                      tasks={tasks
                                        .filter(task => task.objective_key === objective.key)
                                        .sort((a, b) => a.order_index - b.order_index)}
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
                                      className="pl-4 space-y-1 mt-1 mb-4"
                                    />
                                  </div>
                                )}
                              </Draggable>
                            ))}
                          {provided.placeholder}
                          <div className="group flex items-center">
                            <PlusIcon
                              className="invisible group-hover:visible cursor-pointer text-gray-400 hover:text-black add-button h-3 w-3"
                              onClick={() => handleAddObjective(area.key)}
                            />
                          </div>
                        </div>
                      )}
                      </Droppable>
                      <TaskList
                        tasks={tasks
                          .filter((task) => task.area_key === area.key)
                          .sort((a, b) => a.order_index - b.order_index)}
                        parentId={area.key}
                        parentType="area"
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
                        className="space-y-1 mt-4"
                      />
                    </>
                  )}
                </div>
              )}
            </Draggable>
          ))}
          {areas.length === 0 && (
            <div className="flex justify-center">
              <PlusIcon
                className="cursor-pointer text-gray-400 hover:text-black add-button h-4 w-4"
                onClick={handleAddArea}
              />
            </div>
          )}
          {provided.placeholder}
        </div>
      )}
    </Droppable>
  </div>
);

export default AreaList;
