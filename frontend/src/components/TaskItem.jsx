import { Draggable } from '@hello-pangea/dnd'
import { CheckIcon, CircleIcon, Cross2Icon } from '@radix-ui/react-icons'
import ReactMarkdown from 'react-markdown'

const TaskItem = ({
  task,
  index,
  editing,
  onEdit,
  onComplete,
  onDelete,
  onSecondary,
  inputRef,
  onChange,
  onBlur,
  onKeyDown,
  editingTask
}) => (
  <Draggable draggableId={task.key} index={index}>
    {(provided, snapshot) => (
      <div
        ref={provided.innerRef}
        {...provided.draggableProps}
        {...provided.dragHandleProps}
        className={`group flex items-center mb-2 ${snapshot.isDragging ? 'opacity-50' : ''}`}
        onClick={(e) => onEdit(task, e)}
      >
        <div className="flex-grow flex items-center">
          {editing ? (
            <input
              ref={inputRef}
              value={editingTask?.text ?? ''}
              onChange={(e) => onChange(e)}
              onBlur={() => onBlur(task)}
              onKeyDown={onKeyDown}
              className="outline-none font-mate text-sm bg-transparent w-full"
              autoFocus
            />
          ) : (
            <>
              <span
                className={`${task.status === 'complete' ? 'line-through' : ''} ${task.status === 'secondary' ? 'text-gray-400' : ''} flex items-center`}
              >
                • <ReactMarkdown
                    className="inline ml-1"
                    components={{
                      p: ({node, ...props}) => <span {...props} />,
                    }}
                  >
                    {task.text || '_'}
                  </ReactMarkdown>
              </span>
              <div className="invisible group-hover:visible flex items-center ml-4">
                <CheckIcon
                  className="cursor-pointer text-gray-400 hover:text-black h-3 w-3 mr-2"
                  onClick={(e) => onComplete(task, e)}
                />
                {task.status !== 'complete' && (
                  <CircleIcon
                    className={`cursor-pointer h-3 w-3 mr-2 ${
                      task.status === 'secondary' ? 'text-black' : 'text-gray-400 hover:text-black'
                    }`}
                    onClick={(e) => onSecondary(task, e)}
                  />
                )}
                <Cross2Icon
                  className="cursor-pointer text-gray-400 hover:text-black delete-button h-3 w-3"
                  onClick={(e) => onDelete(task.key, e)}
                />
              </div>
            </>
          )}
        </div>
      </div>
    )}
  </Draggable>
)

export default TaskItem

