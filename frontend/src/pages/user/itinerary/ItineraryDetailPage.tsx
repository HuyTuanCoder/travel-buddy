import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Users, Map as MapIcon, ChevronLeft, ChevronRight, Calendar, MessageSquare, Save } from 'lucide-react'
import { APIProvider } from '@vis.gl/react-google-maps'
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd'
import type { DropResult } from '@hello-pangea/dnd'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'
import { useItineraryDetailLogic } from './hooks/useItineraryDetailLogic'
import DayColumn from './components/DayColumn'
import MemberPanel from './components/MemberPanel'
import TripMapVisualizer from './components/TripMapVisualizer'
import VerticalSidebar from './components/VerticalSidebar'
import AIChatPanel from './components/AIChatPanel'
// ==================== Status badge styles (same as TripCard) ====================

const statusStyles: Record<string, string> = {
  DRAFT: 'bg-slate-100 text-slate-600 border-slate-200',
  ACTIVE: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  ARCHIVED: 'bg-amber-50 text-amber-700 border-amber-200',
}

// ==================== Page ====================

export default function ItineraryDetailPage() {
  // Extract itinerary ID from the URL
  const { id } = useParams<{ id: string }>()

  const {
    itinerary,
    draftItinerary,
    isDraftMode,
    toggleDraftMode,
    modifiedStops,
    members,
    isLoading,
    error,
    handleUpdateItinerary,
    handleDeleteItinerary,
    handleAddDay,
    handleRemoveDay,
    addStopDayId,
    setAddStopDayId,
    handleAddStop,
    handleUpdateStop,
    handleRemoveStop,
    handleOptimisticDragDrop,
    handleSwapDays,
    dispatchDraftActions,
    handleDraftDiscard,
    handleDraftSave,
    handleInvite,
    handleRemoveMember,
    handleUpdateMemberRole,
    handleTransferOwnership,
  } = useItineraryDetailLogic(id!)

  const [activeTab, setActiveTab] = useState<string>('')
  
  const [isMembersOpen, setIsMembersOpen] = useState(false)
  const [isTimelineOpen, setIsTimelineOpen] = useState(true)
  const [isMapOpen, setIsMapOpen] = useState(true)
  const [isChatOpen, setIsChatOpen] = useState(true)

  const togglePanel = (panel: 'members' | 'timeline' | 'map' | 'chat') => {
    if (panel === 'members') setIsMembersOpen(!isMembersOpen)
    if (panel === 'timeline') setIsTimelineOpen(!isTimelineOpen)
    if (panel === 'map') setIsMapOpen(!isMapOpen)
    if (panel === 'chat') setIsChatOpen(!isChatOpen)
  }

  useEffect(() => {
    if (itinerary?.days && itinerary.days.length > 0 && !itinerary.days.find(d => d.id === activeTab)) {
      setActiveTab(itinerary.days[0].id)
    }
  }, [itinerary?.days, activeTab])

  const onDragEnd = (result: DropResult) => {
    const { source, destination, draggableId, type } = result
    if (!destination) return

    if (
      source.droppableId === destination.droppableId &&
      source.index === destination.index
    ) {
      return
    }

    if (type === 'DAY') {
      const sourceDay = displayItinerary?.days[source.index];
      const destDay = displayItinerary?.days[destination.index];
      if (sourceDay && destDay) {
        if (isDraftMode) {
          dispatchDraftActions([{ action: 'swap_days', day_a: sourceDay.dayNumber, day_b: destDay.dayNumber }]);
        } else {
          handleSwapDays(sourceDay.dayNumber, destDay.dayNumber);
        }
      }
      return;
    }

    // Pass the exact action to our unified handler
    handleOptimisticDragDrop(
      draggableId, 
      source.droppableId, 
      destination.droppableId, 
      source.index, 
      destination.index
    );
  }

  const displayItinerary = draftItinerary || itinerary

  // --- Loading state ---
  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-12 space-y-6">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-6 w-48" />
          <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
            <div className="space-y-4">
              <Skeleton className="h-48 rounded-2xl" />
              <Skeleton className="h-48 rounded-2xl" />
            </div>
            <Skeleton className="h-72 rounded-2xl" />
          </div>
        </div>
      </main>
    )
  }

  // --- Error or not found ---
  if (!displayItinerary) {
    return (
      <main className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-semibold text-slate-700">
            {error ?? 'Trip not found'}
          </h2>
          <Link to="/trips" className="text-sm text-blue-600 mt-2 inline-block">
            ← Back to trips
          </Link>
        </div>
      </main>
    )
  }

  return (
    <APIProvider apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''}>
      <main className={`min-h-screen text-slate-900 transition-all duration-300 ${isDraftMode ? 'bg-blue-50/30 ring-2 ring-blue-500 shadow-[inset_0_0_20px_rgba(59,130,246,0.1)]' : 'bg-slate-50'}`}>
        <div className="mx-auto max-w-[1400px] px-6 py-8">
        {/* --- Breadcrumb --- */}
        <Link
          to="/trips"
          className="text-xs text-slate-400 hover:text-blue-600 transition-colors"
        >
          ← All trips
        </Link>

        {/* --- Trip header --- */}
        <div className="flex items-start justify-between mt-4 mb-8">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-semibold text-slate-900">
                {displayItinerary.title}
              </h1>
              <Badge
                variant="outline"
                className={statusStyles[displayItinerary.status] ?? ''}
              >
                {displayItinerary.status.toLowerCase()}
              </Badge>
            </div>
            <p className="text-sm text-slate-500">
              {displayItinerary.timezone} · {displayItinerary.days.length} day
              {displayItinerary.days.length !== 1 ? 's' : ''}
            </p>
          </div>

          {/* Trip actions */}
          <div className="flex items-center gap-2">
            <Button
              variant={isDraftMode ? "default" : "outline"}
              className={isDraftMode ? "bg-blue-600 hover:bg-blue-700 text-white" : "border-slate-300 text-slate-700 hover:bg-slate-100"}
              size="sm"
              onClick={() => toggleDraftMode()}
            >
              <div className={`w-2 h-2 rounded-full mr-2 ${isDraftMode ? 'bg-green-400' : 'bg-slate-400'}`}></div>
              Draft Mode: {isDraftMode ? 'ON' : 'OFF'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleUpdateItinerary({
                  status: displayItinerary.status === 'ACTIVE' ? 'ARCHIVED' : 'ACTIVE',
                })
              }
            >
              {displayItinerary.status === 'ACTIVE' ? 'Archive' : 'Activate'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="text-red-500 border-red-200 hover:bg-red-50"
              onClick={handleDeleteItinerary}
            >
              Delete
            </Button>
          </div>
        </div>

        {/* --- Error banner --- */}
        {error && (
          <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {error}
          </div>
        )}

        <Separator className="mb-6" />

        <Separator className="mb-6" />

        {/* --- Main content: Leetcode-style 3-column layout --- */}
        <div className="h-[calc(100vh-160px)] w-full rounded-xl border border-slate-200 shadow-sm bg-white overflow-hidden flex">
          
          {/* GLOBAL LEFT NAV */}
          <VerticalSidebar
            tabs={[
              {
                id: 'members',
                label: 'Members',
                icon: Users,
                onClick: () => togglePanel('members'),
                isActive: isMembersOpen
              },
              {
                id: 'timeline',
                label: 'Timeline',
                icon: Calendar,
                onClick: () => togglePanel('timeline'),
                isActive: isTimelineOpen
              },
              {
                id: 'map',
                label: 'Map View',
                icon: MapIcon,
                onClick: () => togglePanel('map'),
                isActive: isMapOpen
              },
              {
                id: 'chat',
                label: 'AI Assistant',
                icon: MessageSquare,
                onClick: () => togglePanel('chat'),
                isActive: isChatOpen
              }
            ]}
          />

          <ResizablePanelGroup orientation="horizontal" className="flex-1 h-full w-full items-stretch">
            
            {/* Left Column: Sidebar (Members) */}
            {isMembersOpen && (
                <ResizablePanel 
                  defaultSize={20} 
                  minSize={15} 
                  className="bg-slate-50/50 flex flex-col"
                >
                  <div className="h-10 flex items-center justify-between px-3 border-b border-slate-200 bg-white shrink-0">
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                      <Users size={14} />
                      Members
                    </div>
                    <button onClick={() => togglePanel('members')} className="text-slate-400 hover:text-slate-700 p-1 rounded hover:bg-slate-100 transition-colors">
                      <ChevronLeft size={16} />
                    </button>
                  </div>
                  <div className="flex-1 overflow-y-auto hide-scrollbar p-4 space-y-6">
                    {members && (
                      <MemberPanel
                        members={members}
                        onInvite={handleInvite}
                        onRemoveMember={handleRemoveMember}
                        onUpdateRole={handleUpdateMemberRole}
                        onTransferOwnership={handleTransferOwnership}
                      />
                    )}
                  </div>
                </ResizablePanel>
            )}

            {/* Handle before Timeline */}
            {isTimelineOpen && isMembersOpen && <ResizableHandle withHandle />}

            {/* Middle Column: Day Timeline */}
            {isTimelineOpen && (
                <ResizablePanel 
                  defaultSize={40} 
                  minSize={25} 
                  className="flex flex-col bg-white h-full relative z-10"
                >
                  {/* Custom Tab Navigation */}
                  <div className="h-10 flex w-full items-center justify-between border-b border-slate-200 px-3 shrink-0 bg-slate-50/80">
                    <div className="flex items-center overflow-x-auto hide-scrollbar gap-2">
                      {displayItinerary.days.map((day, idx) => (
                        <a
                          key={day.id}
                          href={`#day-${day.id}`}
                          onClick={() => setActiveTab(day.id)}
                          className={`pb-1 font-medium text-sm transition-colors relative whitespace-nowrap shrink-0 px-2 mt-1 ${
                            activeTab === day.id ? 'text-blue-600' : 'text-slate-500 hover:text-slate-800'
                          }`}
                        >
                          Day {idx + 1}
                          {activeTab === day.id && (
                            <span className="absolute -bottom-2 left-0 right-0 h-0.5 bg-blue-600 rounded-t-full" />
                          )}
                        </a>
                      ))}
                    </div>
                    
                    {/* Actions: Save, Add Day & Collapse */}
                    <div className="flex items-center gap-2 shrink-0">
                      {Object.keys(modifiedStops).length > 0 && (
                        <div className="flex items-center gap-1 mr-2 border-r border-slate-200 pr-3 animate-in fade-in">
                          <button
                            onClick={handleDraftDiscard}
                            className="text-xs font-semibold text-slate-500 hover:text-slate-700 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-full transition-colors whitespace-nowrap"
                          >
                            Discard
                          </button>
                          <button
                            onClick={handleDraftSave}
                            disabled={isLoading}
                            className="flex items-center text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 px-3 py-1.5 rounded-full transition-colors whitespace-nowrap shadow-sm disabled:opacity-50"
                          >
                            <Save size={12} className="mr-1.5" />
                            {isLoading ? "Saving..." : "Save"}
                          </button>
                        </div>
                      )}
                      
                      <button
                        onClick={() => handleAddDay({ scheduledDate: null })}
                        className="text-xs font-semibold text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-full transition-colors whitespace-nowrap"
                      >
                        + Add Day
                      </button>
                      <button onClick={() => togglePanel('timeline')} className="text-slate-400 hover:text-slate-700 p-1 rounded hover:bg-slate-100 transition-colors">
                        <ChevronLeft size={16} />
                      </button>
                    </div>
                  </div>

                  <div className="flex-1 w-full overflow-y-auto hide-scrollbar p-6 bg-slate-50/30 scroll-smooth">
                    <DragDropContext onDragEnd={onDragEnd}>
                      <Droppable droppableId="board" type="DAY" direction="vertical">
                        {(provided) => (
                          <div className="space-y-8 pb-20" ref={provided.innerRef} {...provided.droppableProps}>
                            {displayItinerary.days.map((day, index) => (
                              <Draggable key={day.id} draggableId={day.id} index={index}>
                                {(dragProvided) => (
                                  <div 
                                    id={`day-${day.id}`}
                                    ref={dragProvided.innerRef}
                                    {...dragProvided.draggableProps}
                                    className="animate-in fade-in slide-in-from-bottom-2 duration-300 w-full"
                                  >
                                    <DayColumn
                                      day={day}
                                      modifiedStops={modifiedStops}
                                      onRemoveDay={handleRemoveDay}
                                      onAddStop={(dayId, payload) => isDraftMode ? dispatchDraftActions([{ action: 'add', day_number: day.dayNumber, ...payload }]) : handleAddStop(dayId, payload)}
                                      onUpdateStop={(stopId, payload) => isDraftMode ? dispatchDraftActions([{ action: 'update', id: stopId, day_number: day.dayNumber, ...payload }]) : handleUpdateStop(stopId, payload)}
                                      onRemoveStop={(stopId) => isDraftMode ? dispatchDraftActions([{ action: 'remove', id: stopId, day_number: day.dayNumber }]) : handleRemoveStop(stopId)}
                                      isDraftMode={isDraftMode}
                                      onRestoreDay={(dayId) => dispatchDraftActions([{ action: 'restore_day', id: dayId, day_number: day.dayNumber }])}
                                      onRestoreStop={(stopId) => dispatchDraftActions([{ action: 'restore_stop', id: stopId, day_number: day.dayNumber }])}
                                      onHardRemoveStop={(stopId) => dispatchDraftActions([{ action: 'hard_remove', id: stopId, day_number: day.dayNumber }])}
                                      isAddStopOpen={addStopDayId === day.id}
                                      onToggleAddStop={() =>
                                        setAddStopDayId(addStopDayId === day.id ? null : day.id)
                                      }
                                      dragHandleProps={dragProvided.dragHandleProps}
                                    />
                                  </div>
                                )}
                              </Draggable>
                            ))}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </DragDropContext>
                  </div>
                </ResizablePanel>
            )}

            {/* Handle before Map */}
            {isMapOpen && (isMembersOpen || isTimelineOpen) && <ResizableHandle withHandle />}

            {/* Right Column: Sticky Map */}
            {isMapOpen && (
                <ResizablePanel 
                  defaultSize={35} 
                  minSize={20} 
                  className="flex flex-col relative h-full bg-slate-100"
                >
                  <div className="h-10 flex items-center justify-between px-3 border-b border-slate-200 bg-white shrink-0 z-10">
                    <button onClick={() => togglePanel('map')} className="text-slate-400 hover:text-slate-700 p-1 rounded hover:bg-slate-100 transition-colors">
                      <ChevronRight size={16} />
                    </button>
                    <div className="flex flex-1 items-center justify-end gap-1 ml-4">
                      <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-800">
                        Map View
                        <MapIcon size={12} />
                      </div>
                    </div>
                  </div>
                  <div className="flex-1 relative overflow-y-auto bg-white">
                    <TripMapVisualizer itinerary={displayItinerary} />
                  </div>
                </ResizablePanel>
            )}

            {/* Handle before Chat */}
            {isChatOpen && (isMembersOpen || isTimelineOpen || isMapOpen) && <ResizableHandle withHandle />}

            {/* Far Right Column: AI Chat Panel */}
            {isChatOpen && (
                <ResizablePanel
                  defaultSize={25}
                  minSize={20}
                  className="h-full"
                >
                  <AIChatPanel 
                    tripId={id!} 
                    workspaceDraft={displayItinerary}
                    modifiedStops={modifiedStops}
                    isDraftMode={isDraftMode}
                    onDraftReceived={(draftStops) => {
                      dispatchDraftActions(draftStops);
                    }}
                  />
                </ResizablePanel>
            )}

            {!isMembersOpen && !isTimelineOpen && !isMapOpen && !isChatOpen && (
              <div className="flex-1 h-full bg-slate-50 flex items-center justify-center">
                <div className="text-center">
                  <MapIcon size={48} className="text-slate-300 mx-auto mb-4" />
                  <h3 className="text-slate-500 font-medium">No panels open</h3>
                  <p className="text-slate-400 text-sm mt-1">Select a tab from the left menu to view content.</p>
                </div>
              </div>
            )}
          </ResizablePanelGroup>
        </div>
        </div>
      </main>
    </APIProvider>
  )
}


