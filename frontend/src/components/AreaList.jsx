import React from 'react';
import { Droppable, Draggable } from '@hello-pangea/dnd';
import { ChevronDownIcon, ChevronRightIcon, Cross2Icon, PlusIcon, CheckIcon } from '@radix-ui/react-icons';
import ReactMarkdown from 'react-markdown';

const AreaList = ({
  areas,
  objectives,
  collapsedAreas,
  editingArea,
  editingObjective,
  editInputRef,
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
  handleAddObjective
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
                                    {...provided.dragHandleProps}
                                    className={`group flex items-center ${snapshot.isDragging ? 'opacity-50' : ''}`}
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
                  )}
                </div>
              )}
            </Draggable>
          ))}
          {provided.placeholder}
          <div className="mt-4 group flex items-center">
            <PlusIcon
              className="cursor-pointer text-gray-400 hover:text-black add-button h-3 w-3"
              onClick={handleAddArea}
            />
          </div>
        </div>
      )}
    </Droppable>
  </div>
);

export default AreaList;
