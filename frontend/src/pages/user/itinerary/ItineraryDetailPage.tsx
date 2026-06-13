import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import type { PanelImperativeHandle } from "react-resizable-panels"
import { Users, Map as MapIcon, ChevronLeft, ChevronRight, PlusCircle, Calendar } from 'lucide-react'
import { APIProvider } from '@vis.gl/react-google-maps'
import { DragDropContext } from '@hello-pangea/dnd'
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
import AddStopForm from './components/AddStopForm'
import MemberPanel from './components/MemberPanel'
import TripMapVisualizer from './components/TripMapVisualizer'
import VerticalSidebar from './components/VerticalSidebar'

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
    handleReorderStops,
    handleInvite,
    handleRemoveMember,
    handleUpdateMemberRole,
    handleTransferOwnership,
  } = useItineraryDetailLogic(id!)

  const [activeTab, setActiveTab] = useState<string>('')
  
  const [isMembersOpen, setIsMembersOpen] = useState(false)
  const [isTimelineOpen, setIsTimelineOpen] = useState(true)
  const [isMapOpen, setIsMapOpen] = useState(true)

  const togglePanel = (panel: 'members' | 'timeline' | 'map') => {
    if (panel === 'members') setIsMembersOpen(!isMembersOpen)
    if (panel === 'timeline') setIsTimelineOpen(!isTimelineOpen)
    if (panel === 'map') setIsMapOpen(!isMapOpen)
  }

  useEffect(() => {
    if (itinerary?.days && itinerary.days.length > 0 && !itinerary.days.find(d => d.id === activeTab)) {
      setActiveTab(itinerary.days[0].id)
    }
  }, [itinerary?.days, activeTab])

  const onDragEnd = (result: DropResult) => {
    const { source, destination } = result
    if (!destination) return

    if (
      source.droppableId === destination.droppableId &&
      source.index === destination.index
    ) {
      return
    }

    if (source.droppableId !== destination.droppableId) {
      alert('Moving stops between days is not yet supported.')
      return
    }

    if (!itinerary) return

    const day = itinerary.days.find((d) => d.id === source.droppableId)
    if (!day) return

    const newStops = Array.from(day.stops)
    const [movedStop] = newStops.splice(source.index, 1)
    newStops.splice(destination.index, 0, movedStop)

    const stopIds = newStops.map((s) => s.id)
    handleReorderStops(source.droppableId, { stopIds })
  }

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
  if (!itinerary) {
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
      <main className="min-h-screen bg-slate-50 text-slate-900">
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
                {itinerary.title}
              </h1>
              <Badge
                variant="outline"
                className={statusStyles[itinerary.status] ?? ''}
              >
                {itinerary.status.toLowerCase()}
              </Badge>
            </div>
            <p className="text-sm text-slate-500">
              {itinerary.timezone} · {itinerary.days.length} day
              {itinerary.days.length !== 1 ? 's' : ''}
            </p>
          </div>

          {/* Trip actions */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleUpdateItinerary({
                  status: itinerary.status === 'ACTIVE' ? 'ARCHIVED' : 'ACTIVE',
                })
              }
            >
              {itinerary.status === 'ACTIVE' ? 'Archive' : 'Activate'}
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
            position="left"
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
              }
            ]}
          />

          <ResizablePanelGroup orientation="horizontal" className="flex-1 h-full w-full items-stretch">
            
            {/* Left Column: Sidebar (Members) */}
            {isMembersOpen && (
              <>
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
                {(isTimelineOpen || isMapOpen) && <ResizableHandle withHandle />}
              </>
            )}

            {/* Middle Column: Day Timeline */}
            {isTimelineOpen && (
              <>
                <ResizablePanel 
                  defaultSize={isMapOpen ? 50 : 100} 
                  minSize={30} 
                  className="flex flex-col bg-white h-full relative z-10"
                >
                  {/* Custom Tab Navigation */}
                  <div className="h-10 flex w-full items-center justify-between border-b border-slate-200 px-3 shrink-0 bg-slate-50/80">
                    <div className="flex items-center overflow-x-auto hide-scrollbar gap-2">
                      {itinerary.days.map((day, idx) => (
                        <button
                          key={day.id}
                          onClick={() => setActiveTab(day.id)}
                          className={`pb-1 font-medium text-sm transition-colors relative whitespace-nowrap shrink-0 px-2 mt-1 ${
                            activeTab === day.id ? 'text-blue-600' : 'text-slate-500 hover:text-slate-800'
                          }`}
                        >
                          Day {idx + 1}
                          {activeTab === day.id && (
                            <span className="absolute -bottom-2 left-0 right-0 h-0.5 bg-blue-600 rounded-t-full" />
                          )}
                        </button>
                      ))}
                    </div>
                    
                    {/* Actions: Add Day & Collapse */}
                    <div className="flex items-center gap-2 shrink-0">
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

                  <div className="flex-1 w-full overflow-y-auto hide-scrollbar p-6 bg-slate-50/30">
                    <DragDropContext onDragEnd={onDragEnd}>
                      {itinerary.days
                        .filter((day) => day.id === activeTab)
                        .map((day) => (
                          <div key={day.id} className="animate-in fade-in slide-in-from-bottom-2 duration-300 w-full">
                            <DayColumn
                              day={day}
                              onRemoveDay={handleRemoveDay}
                              onAddStop={handleAddStop}
                              onUpdateStop={handleUpdateStop}
                              onRemoveStop={handleRemoveStop}
                              isAddStopOpen={addStopDayId === day.id}
                              onToggleAddStop={() =>
                                setAddStopDayId(addStopDayId === day.id ? null : day.id)
                              }
                            />
                          </div>
                        ))}
                    </DragDropContext>
                  </div>
                </ResizablePanel>
                {isMapOpen && <ResizableHandle withHandle />}
              </>
            )}

            {/* Right Column: Sticky Map */}
            {isMapOpen && (
              <ResizablePanel 
                defaultSize={30} 
                minSize={25} 
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
                  <TripMapVisualizer itinerary={itinerary} />
                </div>
              </ResizablePanel>
            )}

            {!isMembersOpen && !isTimelineOpen && !isMapOpen && (
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


