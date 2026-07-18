import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Dict, Any, List, Optional

# Initialize Firebase/Firestore Admin SDK
if not firebase_admin._apps:
    # Uses local ADC or cloud-native environment metadata
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': os.getenv("GCP_PROJECT", "five-days-final-project")
    })

db = firestore.client()

# Collection names
REQUESTS_COLLECTION = "itinerary_requests"
PENDING_COLLECTION = "pending_approvals"
APPROVED_COLLECTION = "approved_itineraries"


def create_itinerary_request(request_id: str, user_id: str, session_id: str, query: str) -> Dict[str, Any]:
    """
    Creates a new itinerary request in Firestore with 'processing' status.
    """
    doc_ref = db.collection(REQUESTS_COLLECTION).document(request_id)
    data = {
        "request_id": request_id,
        "user_id": user_id,
        "session_id": session_id,
        "query": query,
        "status": "processing",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "logs": ["Initialized itinerary planner request thread."],
        "itinerary": None,
        "evaluation": None
    }
    doc_ref.set(data)
    return data


def add_request_log(request_id: str, log_message: str) -> None:
    """
    Appends a log message to the log stream of an active request.
    """
    doc_ref = db.collection(REQUESTS_COLLECTION).document(request_id)
    doc_ref.update({
        "logs": firestore.ArrayUnion([f"[{datetime.utcnow().strftime('%H:%M:%S')}] {log_message}"]),
        "updated_at": datetime.utcnow().isoformat()
    })


def get_itinerary_request(request_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a specific itinerary request.
    """
    doc_ref = db.collection(REQUESTS_COLLECTION).document(request_id)
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else None


def update_request_status(request_id: str, status: str, itinerary: Optional[Dict[str, Any]] = None, evaluation: Optional[Dict[str, Any]] = None) -> None:
    """
    Updates status, itinerary proposal, and evaluation results.
    """
    doc_ref = db.collection(REQUESTS_COLLECTION).document(request_id)
    updates = {
        "status": status,
        "updated_at": datetime.utcnow().isoformat()
    }
    if itinerary is not None:
        updates["itinerary"] = itinerary
    if evaluation is not None:
        updates["evaluation"] = evaluation
        
    doc_ref.update(updates)


def move_to_pending_approval(request_id: str, user_id: str, session_id: str, query: str, itinerary: Dict[str, Any], evaluation: Dict[str, Any]) -> None:
    """
    Stores an itinerary proposal under pending approvals for admin evaluation review.
    """
    doc_ref = db.collection(PENDING_COLLECTION).document(request_id)
    doc_ref.set({
        "request_id": request_id,
        "user_id": user_id,
        "session_id": session_id,
        "query": query,
        "itinerary": itinerary,
        "evaluation": evaluation,
        "created_at": datetime.utcnow().isoformat()
    })
    update_request_status(request_id, "pending_approval", itinerary, evaluation)


def get_pending_approvals() -> List[Dict[str, Any]]:
    """
    Lists all pending approvals for the administrator dashboard.
    """
    docs = db.collection(PENDING_COLLECTION).order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    return [doc.to_dict() for doc in docs]


def approve_itinerary(request_id: str) -> bool:
    """
    Approves an itinerary proposal, moving it to approved_itineraries and cleaning pending.
    """
    pending_ref = db.collection(PENDING_COLLECTION).document(request_id)
    pending_doc = pending_ref.get()
    
    if not pending_doc.exists:
        return False
        
    pending_data = pending_doc.to_dict()
    
    # Write to approved_itineraries
    approved_ref = db.collection(APPROVED_COLLECTION).document(request_id)
    approved_ref.set({
        "request_id": request_id,
        "user_id": pending_data["user_id"],
        "session_id": pending_data["session_id"],
        "query": pending_data["query"],
        "itinerary": pending_data["itinerary"],
        "approved_at": datetime.utcnow().isoformat()
    })
    
    # Delete from pending_approvals
    pending_ref.delete()
    
    # Update main request status
    update_request_status(request_id, "approved")
    add_request_log(request_id, "Proposal approved by administrator.")
    return True


def reject_itinerary(request_id: str, reason: Optional[str] = None) -> bool:
    """
    Rejects an itinerary proposal, deleting it from pending and updating main status.
    """
    pending_ref = db.collection(PENDING_COLLECTION).document(request_id)
    if not pending_ref.get().exists:
        return False
        
    # Delete from pending_approvals
    pending_ref.delete()
    
    # Update status to rejected
    update_request_status(request_id, "rejected")
    reject_msg = f"Proposal rejected by administrator."
    if reason:
        reject_msg += f" Reason: {reason}"
    add_request_log(request_id, reject_msg)
    return True
