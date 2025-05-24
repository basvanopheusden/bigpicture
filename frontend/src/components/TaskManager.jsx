import React, { useState, useEffect, useRef } from 'react';
import { DragDropContext } from '@hello-pangea/dnd';
import AreaList from './AreaList';
import { ChevronDownIcon, ChevronRightIcon } from '@radix-ui/react-icons';
import { v4 as uuidv4 } from 'uuid';
import apiWrapper from '../api';
import ReactMarkdown from 'react-markdown';
import { getStoredAuth, storeAuth, clearAuth } from '../utils/auth';
import { divSpec, specToReact } from '../utils/divBuilder';
const TaskManager = () => {
    const [authenticated, setAuthenticated] = useState(false);
    const [passcode, setPasscode] = useState('');
    const [areas, setAreas] = useState([]);
    const [objectives, setObjectives] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [editingArea, setEditingArea] = useState(null);
    const [editingAreaBottom, setEditingAreaBottom] = useState(null);
    const [editingObjective, setEditingObjective] = useState(null);
    const [editingTask, setEditingTask] = useState(null);
    const [lastKeyDown, setLastKeyDown] = useState(null);
    const [error, setError] = useState(null);
    const [collapsedAreas, setCollapsedAreas] = useState(() => {
      const stored = localStorage.getItem('collapsedAreas');
      return new Set(stored ? JSON.parse(stored) : []);
    });
    const editInputRef = useRef(null);
    const editInputBottomRef = useRef(null);

    useEffect(() => {
      if (getStoredAuth()) {
        setAuthenticated(true);
      }
    }, []);
  
    useEffect(() => {
      if (authenticated) {
        refreshAll();
      }
    }, [authenticated]);
  
    useEffect(() => {
      if (editingArea || editingObjective) {
        editInputRef.current?.focus();
      }
    }, [editingArea, editingObjective]);
  
    useEffect(() => {
      if (editingAreaBottom || editingTask) {
        editInputBottomRef.current?.focus();
      }
    }, [editingAreaBottom, editingTask]);
  
    useEffect(() => {
      const handleKeyDown = (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
          e.preventDefault();
          handleUndo();
        }
      };

      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    useEffect(() => {
      localStorage.setItem('collapsedAreas', JSON.stringify([...collapsedAreas]));
    }, [collapsedAreas]);
  
    const refreshAll = async () => {
      try {
        setError(null);
        console.log('Starting data refresh...');
        
        const [areasData, objectivesData, tasksData] = await Promise.all([
          apiWrapper.get('/api/areas'),
          apiWrapper.get('/api/objectives'),
          apiWrapper.get('/api/tasks')
        ]);
        
        console.log('Received data:', {
          areas: areasData,
          objectives: objectivesData,
          tasks: tasksData
        });
        
        setAreas(areasData.sort((a, b) => a.order_index - b.order_index));
        setObjectives(objectivesData.sort((a, b) => a.order_index - b.order_index));
        setTasks(tasksData.sort((a, b) => a.order_index - b.order_index));
        
        console.log('State updated with:', {
          areas: areasData.length,
          objectives: objectivesData.length,
          tasks: tasksData.length
        });
      } catch (error) {
        console.error('Error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        });
        setError('Failed to load data. Please refresh the page.');
      }
    };
  
    const handleUndo = async () => {
      try {
        await apiWrapper.post('/api/undo');
        await refreshAll();
      } catch (error) {
        console.error('Failed to undo:', error);
      }
    };
  
    const handleKeyPress = (event) => {
      if (event.key === 'Enter') {
        if (passcode === 'sneeze') {
          setAuthenticated(true);
          storeAuth();
        } else {
          setPasscode('');
        }
      }
    };

    const handleLogout = () => {
      clearAuth();
      setAuthenticated(false);
    };
// Area handlers
const handleAreaClick = (area, event, isBottom = false) => {
    if (event.target.closest('.delete-button') || event.target.closest('.add-button')) return;
    if (isBottom) return;
    
    setEditingArea({ ...area });
    setEditingObjective(null);
  };

  const handleAreaBlur = async () => {
    if (!editingArea) return;
    
    try {
      if (!editingArea.text.trim() && lastKeyDown === 'Backspace') {
        await handleDeleteArea(editingArea.key, new Event('dummy'));
      } else {
        await apiWrapper.patch(`/api/areas/${editingArea.key}`, {
          text: editingArea.text
        });
        await refreshAll();
      }
    } catch (error) {
      console.error('Failed to update area:', error);
    } finally {
      setEditingArea(null);
    }
  };

  const handleAddArea = async () => {
    try {
      const newArea = {
        key: uuidv4(),
        text: ''
      };
      await apiWrapper.post('/api/areas', newArea);
      await refreshAll();
      setEditingArea(newArea);
    } catch (error) {
      console.error('Failed to create area:', error);
    }
  };

  const handleDeleteArea = async (areaKey, e) => {
    e.stopPropagation();
    try {
      await apiWrapper.delete(`/api/areas/${areaKey}`);
      await refreshAll();
    } catch (error) {
      console.error('Failed to delete area:', error);
    }
  };

  const toggleAreaCollapse = (key) => {
    setCollapsedAreas(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  // Objective handlers
  const handleObjectiveClick = (objective, event, isBottom = false) => {
    if (event.target.closest('.delete-button') || event.target.closest('.add-button')) return;
    if (isBottom) return;
    
    setEditingObjective({ ...objective });
    setEditingArea(null);
  };

  const handleObjectiveBlur = async () => {
    if (!editingObjective) return;
    
    try {
      if (!editingObjective.text.trim() && lastKeyDown === 'Backspace') {
        await handleDeleteObjective(editingObjective.key, new Event('dummy'));
      } else {
        await apiWrapper.patch(`/api/objectives/${editingObjective.key}`, {
          text: editingObjective.text
        });
        await refreshAll();
      }
    } catch (error) {
      console.error('Failed to update objective:', error);
    } finally {
      setEditingObjective(null);
    }
  };

  const handleAddObjective = async (areaKey) => {
    try {
      const newObjective = {
        key: uuidv4(),
        area_key: areaKey,
        text: ''
      };
      await apiWrapper.post('/api/objectives', newObjective);
      await refreshAll();
      setEditingObjective(newObjective);
    } catch (error) {
      console.error('Failed to create objective:', error);
    }
  };

  const handleDeleteObjective = async (objectiveKey, e) => {
    e.stopPropagation();
    try {
      await apiWrapper.delete(`/api/objectives/${objectiveKey}`);
      await refreshAll();
    } catch (error) {
      console.error('Failed to delete objective:', error);
    }
  };

  const handleCompleteObjective = async (objective, e) => {
    e.stopPropagation();
    try {
      const newStatus = objective.status === 'complete' ? 'open' : 'complete';
      await apiWrapper.patch(`/api/objectives/${objective.key}`, {
        status: newStatus
      });
      await refreshAll();
    } catch (error) {
      console.error('Failed to update objective status:', error);
    }
  };
// Task handlers
const handleTaskClick = (task, event) => {
  if (event.target.closest('.delete-button') || event.target.closest('.add-button')) return;
  setEditingTask({
    key: task.key,
    text: task.text || '',  // Explicitly set text
    area_key: task.area_key,
    objective_key: task.objective_key
  });
  setEditingAreaBottom(null);
};

  const handleTaskBlur = async (task) => {
    if (!editingTask) return;
    
    try {
      if (!editingTask.text.trim()) {
        await handleDeleteTask(task.key, new Event('dummy'));
      } else {
        const response = await apiWrapper.patch(`/api/tasks/${task.key}`, {
          text: editingTask.text
        });
        setTasks(prevTasks => 
          prevTasks.map(t => t.key === task.key ? {...t, text: editingTask.text} : t)
        );
      }
    } catch (error) {
      console.error('Failed to update task:', error);
    } finally {
      setEditingTask(null);
    }
  };

  const handleAddTask = async (parentKey, parentType = 'area') => {
    try {
      const newTask = {
        key: uuidv4(),
        text: '',
        ...(parentType === 'area' 
          ? { area_key: parentKey } 
          : { objective_key: parentKey })
      };
      await apiWrapper.post('/api/tasks', newTask);
      await refreshAll();
      setEditingTask(newTask);
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  const handleDeleteTask = async (taskKey, e) => {
    if (e && e.stopPropagation) {
      e.stopPropagation();
    }
    try {
      setTasks(prevTasks => prevTasks.filter(task => task.key !== taskKey));
      await apiWrapper.delete(`/api/tasks/${taskKey}`);
      await refreshAll();
    } catch (error) {
      console.error('Failed to delete task:', error);
      await refreshAll();
    }
  };

  const handleCompleteTask = async (task, e) => {
    e.stopPropagation();
    try {
      const newStatus = task.status === 'complete' ? 'open' : 'complete';
      await apiWrapper.patch(`/api/tasks/${task.key}`, {
        status: newStatus
      });
      await refreshAll();
    } catch (error) {
      console.error('Failed to update task status:', error);
    }
  };

  const handleSecondaryTask = async (task, e) => {
    e.stopPropagation();
    try {
      const newStatus = task.status === 'secondary' ? 'open' : 'secondary';
      await apiWrapper.patch(`/api/tasks/${task.key}`, {
        status: newStatus
      });
      await refreshAll();
    } catch (error) {
      console.error('Failed to update task status:', error);
    }
  };

  const onDragEnd = async (result) => {
    const { destination, source, draggableId, type } = result;
    
    if (!destination || (destination.droppableId === source.droppableId && 
        destination.index === source.index)) {
      return;
    }
  
    try {
      if (type === 'area') {
        const newAreas = Array.from(areas);
        const [removed] = newAreas.splice(source.index, 1);
        newAreas.splice(destination.index, 0, removed);
        setAreas(newAreas);
        
        await apiWrapper.patch(`/api/areas/${draggableId}`, {
          order_index: destination.index
        });
      } 
      else if (type === 'objective') {
        const movedObjective = objectives.find(obj => obj.key === draggableId);
        if (!movedObjective) return;
  
        const newObjectives = Array.from(objectives);
        const objIndex = newObjectives.findIndex(obj => obj.key === draggableId);
        const [removed] = newObjectives.splice(objIndex, 1);
        
        const updatedObjective = {
          ...removed,
          area_key: destination.droppableId,
          order_index: destination.index
        };
  
        const insertIndex = newObjectives.findIndex(obj => 
          obj.area_key === destination.droppableId && 
          obj.order_index >= destination.index
        );
        
        if (insertIndex === -1) {
          newObjectives.push(updatedObjective);
        } else {
          newObjectives.splice(insertIndex, 0, updatedObjective);
        }
  
        setObjectives(newObjectives);
  
        await apiWrapper.patch(`/api/objectives/${draggableId}`, {
          area_key: destination.droppableId,
          order_index: destination.index
        });
      }
      else if (type === 'task') {
        const [destParentId, destType] = destination.droppableId.split('-');
        const [sourceParentId, sourceType] = source.droppableId.split('-');
        
        // Find the task being moved
        const taskToMove = tasks.find(t => t.key === draggableId);
        if (!taskToMove) return;
  
        // Create a copy of all tasks
        let newTasks = tasks.filter(t => t.key !== draggableId);
  
        // Adjust order indices for tasks in the source container
        newTasks = newTasks.map(task => {
          if (sourceType === 'area' && task.area_key === sourceParentId && task.order_index > source.index) {
            return { ...task, order_index: task.order_index - 1 };
          }
          if (sourceType === 'objective' && task.objective_key === sourceParentId && task.order_index > source.index) {
            return { ...task, order_index: task.order_index - 1 };
          }
          return task;
        });
  
        // Adjust order indices for tasks in the destination container
        newTasks = newTasks.map(task => {
          if (destType === 'area' && task.area_key === destParentId && task.order_index >= destination.index) {
            return { ...task, order_index: task.order_index + 1 };
          }
          if (destType === 'objective' && task.objective_key === destParentId && task.order_index >= destination.index) {
            return { ...task, order_index: task.order_index + 1 };
          }
          return task;
        });
  
        // Create updated version of moved task
        const updatedTask = {
          ...taskToMove,
          area_key: destType === 'area' ? destParentId : null,
          objective_key: destType === 'objective' ? destParentId : null,
          order_index: destination.index
        };
  
        // Insert the moved task at its new position
        newTasks.splice(destination.index, 0, updatedTask);
  
        // Update state immediately
        setTasks(newTasks);
  
        // Make API call
        await apiWrapper.patch(`/api/tasks/${draggableId}`, {
          area_key: destType === 'area' ? destParentId : null,
          objective_key: destType === 'objective' ? destParentId : null,
          order_index: destination.index
        });
      }
    } catch (error) {
      console.error('Failed to update after drag:', error);
      // On error, refresh from server
      await refreshAll();
    }
  };

// Input handlers
const handleAreaChange = (e) => {
  const cursorPosition = e.target.selectionStart;
  setEditingArea(prev => ({ ...prev, text: e.target.value }));
  setTimeout(() => {
    e.target.setSelectionRange(cursorPosition, cursorPosition);
  }, 0);
};

const handleObjectiveChange = (e) => {
  const cursorPosition = e.target.selectionStart;
  setEditingObjective(prev => ({ ...prev, text: e.target.value }));
  setTimeout(() => {
    e.target.setSelectionRange(cursorPosition, cursorPosition);
  }, 0);
};

const handleTaskChange = (e) => {
  const input = e.target;
  const newValue = input.value;
  const newSelection = input.selectionStart;
  
  setEditingTask(prev => ({
    ...prev,
    text: newValue
  }));
  
  // Give React time to update the DOM
  requestAnimationFrame(() => {
    input.setSelectionRange(newSelection, newSelection);
  });
};

  const handleAreaKeyPress = (e) => {
    setLastKeyDown(e.key);
    if (e.key === 'Enter') {
      editInputRef.current?.blur();
    }
  };

  const handleObjectiveKeyPress = async (e) => {
    setLastKeyDown(e.key);
    if (e.key === 'Backspace' && editingObjective.text === '') {
      e.preventDefault();
      await handleDeleteObjective(editingObjective.key, new Event('dummy'));
      setEditingObjective(null);
      return;
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      const currentObjective = editingObjective;
      
      try {
        await apiWrapper.patch(`/api/objectives/${currentObjective.key}`, {
          text: currentObjective.text
        });
        
        const newObjective = {
          key: uuidv4(),
          area_key: currentObjective.area_key,
          text: ''
        };

        await apiWrapper.post('/api/objectives', newObjective);
        await refreshAll();
        setEditingObjective(newObjective);
      } catch (error) {
        console.error('Failed to handle objective update and creation:', error);
      }
    }
  };

  const handleTaskKeyPress = async (e) => {
    setLastKeyDown(e.key);
    if (e.key === 'Backspace' && editingTask.text === '') {
      e.preventDefault();
      await handleDeleteTask(editingTask.key, new Event('dummy'));
      setEditingTask(null);
      return;
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      const currentTask = editingTask;
      
      try {
        await apiWrapper.patch(`/api/tasks/${currentTask.key}`, {
          text: currentTask.text
        });
        
        const newTask = {
          key: uuidv4(),
          text: ''
        };
        
        if (currentTask.area_key) {
          newTask.area_key = currentTask.area_key;
        } else if (currentTask.objective_key) {
          newTask.objective_key = currentTask.objective_key;
        }

        await apiWrapper.post('/api/tasks', newTask);
        await refreshAll();
        setEditingTask(newTask);
      } catch (error) {
        console.error('Failed to handle task update and creation:', error);
      }
    }
  };

  if (!authenticated) {
    const spec = divSpec({
      className: 'h-screen w-screen flex items-center justify-center font-mate bg-[#f5f5dc]',
      children: [
        divSpec({
          children: (
            <input
              type="password"
              value={passcode}
              onChange={(e) => setPasscode(e.target.value)}
              onKeyPress={handleKeyPress}
              className="border p-2 text-center w-48 outline-none text-sm bg-transparent"
              autoFocus
            />
          )
        })
      ]
    });
    return specToReact(spec, React);
  }

return (
  <div className="min-h-screen h-full flex flex-col text-xs sm:text-sm font-mate min-w-full">
    <DragDropContext
      onDragEnd={(result) => {
        const dragPromise = onDragEnd(result);
        dragPromise
          .then(() => {
            refreshAll();
          })
          .catch((error) => {
            console.error("Error during drag operation:", error);
            refreshAll();
          });
      }}
    >
      <div className="fixed top-4 right-4">
        <button onClick={handleUndo} className="text-gray-400 hover:text-black">
          ↺
        </button>
      </div>

      {error && (
        <div className="fixed top-4 left-4 bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded">
          {error}
        </div>
      )}

      <AreaList
        areas={areas}
        objectives={objectives}
        collapsedAreas={collapsedAreas}
        editingArea={editingArea}
        editingObjective={editingObjective}
        editInputRef={editInputRef}
        handleAreaClick={handleAreaClick}
        toggleAreaCollapse={toggleAreaCollapse}
        handleAreaChange={handleAreaChange}
        handleAreaBlur={handleAreaBlur}
        handleAreaKeyPress={handleAreaKeyPress}
        handleDeleteArea={handleDeleteArea}
        handleAddArea={handleAddArea}
        handleObjectiveClick={handleObjectiveClick}
        handleObjectiveChange={handleObjectiveChange}
        handleObjectiveBlur={handleObjectiveBlur}
        handleObjectiveKeyPress={handleObjectiveKeyPress}
        handleCompleteObjective={handleCompleteObjective}
        handleDeleteObjective={handleDeleteObjective}
        handleAddObjective={handleAddObjective}
        tasks={tasks}
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
      />

    </DragDropContext>
  </div>
);
};

export default TaskManager;
