export const ensureDayExists = (draft: any, dayNum: number, itineraryId: string) => {
    let day = draft.days.find((d: any) => d.dayNumber === dayNum);
    if (!day) {
        const currentMax = draft.days.length > 0 ? Math.max(...draft.days.map((d: any) => d.dayNumber)) : 0;
        for (let i = currentMax + 1; i <= dayNum; i++) {
            draft.days.push({
                id: `ai-temp-day-${crypto.randomUUID()}`,
                itineraryId,
                dayNumber: i,
                scheduledDate: null,
                stops: [],
                isDraftDeleted: false
            });
        }
        day = draft.days.find((d: any) => d.dayNumber === dayNum);
    }
    return day;
};

export const applyDraftAction = (draft: any, action: any, modifiedStops: any, itineraryId: string) => {
    const type = action.action;
    
    if (type === 'add') {
        const targetDay = ensureDayExists(draft, action.day_number, itineraryId);
        if (targetDay) {
            const tempId = action.id || `ai-temp-${crypto.randomUUID()}`;
            targetDay.stops.push({
                id: tempId,
                googlePlaceId: action.google_place_id,
                locationName: action.name || action.place_name || '',
                stopType: action.stop_type || 'ATTRACTION',
                userNotes: action.user_notes || '',
                arrivalTime: action.arrival_time || null,
                departureTime: action.departure_time || null,
                estimatedCost: action.estimated_cost ? parseFloat(action.estimated_cost) : null,
                isDraftDeleted: false
            });
            if (!modifiedStops[tempId]) modifiedStops[tempId] = {};
            modifiedStops[tempId].isAiModified = true;
        }
    }
    else if (type === 'remove') {
        const targetDay = draft.days.find((d: any) => d.dayNumber === action.day_number);
        if (targetDay) {
            const targetStop = targetDay.stops.find((s: any) => s.googlePlaceId === action.google_place_id || s.id === action.id);
            if (targetStop) {
                targetStop.isDraftDeleted = true; // Tombstone
                if (!modifiedStops[targetStop.id]) modifiedStops[targetStop.id] = {};
                modifiedStops[targetStop.id].isAiModified = true;
            }
        }
    }
    else if (type === 'hard_remove') {
        const targetDay = draft.days.find((d: any) => d.dayNumber === action.day_number);
        if (targetDay) {
            targetDay.stops = targetDay.stops.filter((s: any) => s.id !== action.id);
        }
    }
    else if (type === 'update') {
        const targetDay = draft.days.find((d: any) => d.dayNumber === action.day_number);
        if (targetDay) {
            const targetStop = targetDay.stops.find((s: any) => s.googlePlaceId === action.google_place_id || s.id === action.id);
            if (targetStop) {
                if (action.user_notes !== undefined) targetStop.userNotes = action.user_notes;
                if (action.arrival_time !== undefined) targetStop.arrivalTime = action.arrival_time;
                if (action.departure_time !== undefined) targetStop.departureTime = action.departure_time;
                if (!modifiedStops[targetStop.id]) modifiedStops[targetStop.id] = {};
                modifiedStops[targetStop.id].isAiModified = true;
            }
        }
    }
    else if (type === 'move') {
        const oldDay = draft.days.find((d: any) => d.dayNumber === action.old_day_number);
        const newDay = ensureDayExists(draft, action.new_day_number, itineraryId);
        
        if (oldDay && newDay) {
            const targetIndex = oldDay.stops.findIndex((s: any) => s.googlePlaceId === action.google_place_id || s.id === action.id);
            if (targetIndex !== -1) {
                const [movedStop] = oldDay.stops.splice(targetIndex, 1);
                if (action.new_visit_order !== undefined && action.new_visit_order !== null) {
                    newDay.stops.splice(action.new_visit_order, 0, movedStop);
                } else {
                    newDay.stops.push(movedStop);
                }
                if (!modifiedStops[movedStop.id]) modifiedStops[movedStop.id] = {};
                modifiedStops[movedStop.id].isAiModified = true;
            }
        }
    }
    else if (type === 'add_day') {
        const targetDay = ensureDayExists(draft, action.day_number, itineraryId);
        if (targetDay && action.scheduled_date) {
            targetDay.scheduledDate = action.scheduled_date;
        }
    }
    else if (type === 'remove_day') {
        const targetDay = draft.days.find((d: any) => d.dayNumber === action.day_number || d.id === action.id);
        if (targetDay) targetDay.isDraftDeleted = true; // Tombstone
    }
    else if (type === 'restore_day') {
        const targetDay = draft.days.find((d: any) => d.dayNumber === action.day_number || d.id === action.id);
        if (targetDay) targetDay.isDraftDeleted = false; // Restore
    }
    else if (type === 'restore_stop') {
        const targetDay = draft.days.find((d: any) => d.dayNumber === action.day_number || d.id === action.day_id);
        if (targetDay) {
            const targetStop = targetDay.stops.find((s: any) => s.googlePlaceId === action.google_place_id || s.id === action.id);
            if (targetStop) targetStop.isDraftDeleted = false; // Restore
        }
    }
    else if (type === 'swap_days') {
        const dayAIndex = draft.days.findIndex((d: any) => d.dayNumber === action.day_a);
        const dayBIndex = draft.days.findIndex((d: any) => d.dayNumber === action.day_b);
        if (dayAIndex !== -1 && dayBIndex !== -1) {
            const temp = draft.days[dayAIndex].dayNumber;
            draft.days[dayAIndex].dayNumber = draft.days[dayBIndex].dayNumber;
            draft.days[dayBIndex].dayNumber = temp;
        }
    }
};
