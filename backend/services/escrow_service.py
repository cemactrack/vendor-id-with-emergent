from typing import Dict, List, Optional, Tuple, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.escrow_models import *
from datetime import datetime, timedelta, timezone
import uuid
import logging
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

class EscrowService:
    """Core escrow service for managing payments, orders, and disputes"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.orders_collection = db.escrow_orders
        self.escrow_collection = db.escrow_accounts
        self.payments_collection = db.payment_instructions
        self.disputes_collection = db.disputes
        self.transactions_collection = db.escrow_transactions
        self.notifications_collection = db.escrow_notifications
        
        # Platform configuration
        self.platform_fee_percentage = 2.5
        self.default_auto_release_days = 7
        self.max_extension_days = 30
    
    # ===== ORDER MANAGEMENT =====
    
    async def create_order(self, customer_id: str, order_data: OrderCreate) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Create a new order with escrow"""
        try:
            # Verify vendor exists
            vendor = await self.db.vendor_profiles.find_one({"vendor_id": order_data.vendor_id})
            if not vendor:
                return False, None, "Vendor not found"
            
            # Verify customer exists
            customer = await self.db.users.find_one({"id": customer_id})
            if not customer:
                return False, None, "Customer not found"
            
            # Generate order ID
            order_id = f"ORD-{uuid.uuid4().hex[:12].upper()}"
            
            # Process order items and calculate totals
            processed_items = []
            subtotal = Decimal('0.00')
            currency = None
            
            for item_data in order_data.items:
                item_id = f"ITM-{uuid.uuid4().hex[:8].upper()}"
                total_price = Decimal(str(item_data.unit_price)) * item_data.quantity
                
                item = OrderItem(
                    item_id=item_id,
                    total_price=float(total_price),
                    **item_data.dict()
                )
                processed_items.append(item)
                subtotal += total_price
                
                # Use currency from first item (all items should have same currency)
                if currency is None:
                    currency = item_data.currency
                elif currency != item_data.currency:
                    return False, None, "All items must use the same currency"
            
            # Calculate platform fee
            platform_fee = subtotal * Decimal(str(self.platform_fee_percentage)) / Decimal('100')
            total_amount = subtotal + platform_fee
            
            # Round to 2 decimal places
            subtotal = float(subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            platform_fee = float(platform_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            total_amount = float(total_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            
            # Create order
            order = Order(
                order_id=order_id,
                customer_id=customer_id,
                vendor_id=order_data.vendor_id,
                items=processed_items,
                subtotal=subtotal,
                platform_fee=platform_fee,
                total_amount=total_amount,
                currency=currency,
                delivery_address=order_data.delivery_address,
                special_instructions=order_data.special_instructions,
                expected_delivery_date=order_data.expected_delivery_date,
                status=OrderStatus.PENDING_PAYMENT,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Save order to database
            order_dict = order.dict()
            await self.orders_collection.insert_one(order_dict)
            
            # Remove MongoDB _id field for JSON serialization
            order_dict.pop('_id', None)
            
            # Generate payment instructions
            payment_instructions = await self._generate_payment_instructions(order)
            
            # Create escrow account (initially waiting for payment)
            escrow = await self._create_escrow_account(order)
            
            # Send notifications
            await self._send_notification(
                customer_id, "customer", EscrowNotificationType.ORDER_CREATED,
                "Order Created", 
                f"Your order {order_id} has been created. Please complete payment to proceed.",
                {"order_id": order_id, "amount": total_amount, "currency": currency.value}
            )
            
            await self._send_notification(
                order_data.vendor_id, "vendor", EscrowNotificationType.ORDER_CREATED,
                "New Order Received",
                f"You have received a new order {order_id}. Payment is pending.",
                {"order_id": order_id, "amount": subtotal, "currency": currency.value}
            )
            
            logger.info(f"Order created successfully: {order_id}")
            
            return True, {
                "order": order_dict,
                "escrow": escrow,
                "payment_instructions": payment_instructions.dict()
            }, None
            
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            return False, None, f"Order creation failed: {str(e)}"
    
    async def _generate_payment_instructions(self, order: Order) -> PaymentInstruction:
        """Generate payment instructions for an order"""
        instruction_id = f"PAY-{uuid.uuid4().hex[:10].upper()}"
        
        # Generate bank details (this would be platform's bank account)
        bank_details = {
            "bank_name": "Platform Escrow Bank",
            "account_name": "Vendor ID Platform Escrow",
            "account_number": "1234567890",
            "routing_code": "ABC123",
            "reference": f"VID-{order.order_id}"
        }
        
        payment_instruction = PaymentInstruction(
            instruction_id=instruction_id,
            order_id=order.order_id,
            payment_method=PaymentMethod.BANK_TRANSFER,
            bank_details=bank_details,
            amount=order.total_amount,
            currency=order.currency,
            status=PaymentStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        # Save payment instruction
        await self.payments_collection.insert_one(payment_instruction.dict())
        
        return payment_instruction
    
    async def _create_escrow_account(self, order: Order) -> Dict[str, Any]:
        """Create escrow account for order"""
        escrow_id = f"ESC-{uuid.uuid4().hex[:10].upper()}"
        
        # Calculate vendor amount (subtract platform fee)
        vendor_amount = order.subtotal
        
        # Set auto-release date
        auto_release_date = datetime.now(timezone.utc) + timedelta(days=self.default_auto_release_days)
        
        escrow = EscrowAccount(
            escrow_id=escrow_id,
            order_id=order.order_id,
            customer_id=order.customer_id,
            vendor_id=order.vendor_id,
            amount=order.total_amount,
            currency=order.currency,
            platform_fee=order.platform_fee,
            vendor_amount=vendor_amount,
            status=EscrowStatus.WAITING_PAYMENT,
            created_at=datetime.now(timezone.utc),
            auto_release_date=auto_release_date
        )
        
        escrow_dict = escrow.dict()
        await self.escrow_collection.insert_one(escrow_dict)
        
        # Remove MongoDB _id field for JSON serialization
        escrow_dict.pop('_id', None)
        
        return escrow_dict
    
    # ===== PAYMENT MANAGEMENT =====
    
    async def submit_payment_proof(self, customer_id: str, payment_data: PaymentProofSubmission) -> Tuple[bool, Optional[str]]:
        """Customer submits payment proof"""
        try:
            # Get payment instruction
            payment_instruction = await self.payments_collection.find_one(
                {"instruction_id": payment_data.instruction_id}
            )
            
            if not payment_instruction:
                return False, "Payment instruction not found"
            
            # Get order
            order = await self.orders_collection.find_one({"order_id": payment_instruction["order_id"]})
            if not order or order["customer_id"] != customer_id:
                return False, "Order not found or unauthorized"
            
            # Update payment instruction with proof
            await self.payments_collection.update_one(
                {"instruction_id": payment_data.instruction_id},
                {
                    "$set": {
                        "reference_number": payment_data.reference_number,
                        "payment_proof": ",".join(payment_data.proof_files),
                        "status": PaymentStatus.SUBMITTED,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Update order status
            await self.orders_collection.update_one(
                {"order_id": order["order_id"]},
                {
                    "$set": {
                        "status": OrderStatus.PAYMENT_SUBMITTED,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Notify vendor and admin
            await self._send_notification(
                order["vendor_id"], "vendor", EscrowNotificationType.PAYMENT_SUBMITTED,
                "Payment Submitted",
                f"Customer has submitted payment proof for order {order['order_id']}. Awaiting confirmation.",
                {"order_id": order["order_id"]}
            )
            
            logger.info(f"Payment proof submitted for order: {order['order_id']}")
            
            return True, "Payment proof submitted successfully. Awaiting confirmation."
            
        except Exception as e:
            logger.error(f"Failed to submit payment proof: {e}")
            return False, "Failed to submit payment proof"
    
    async def confirm_payment(self, admin_id: str, instruction_id: str, confirmed: bool, notes: str = "") -> Tuple[bool, Optional[str]]:
        """Admin confirms or rejects payment"""
        try:
            # Get payment instruction
            payment_instruction = await self.payments_collection.find_one({"instruction_id": instruction_id})
            if not payment_instruction:
                return False, "Payment instruction not found"
            
            # Get order
            order = await self.orders_collection.find_one({"order_id": payment_instruction["order_id"]})
            if not order:
                return False, "Order not found"
            
            if confirmed:
                # Confirm payment
                await self.payments_collection.update_one(
                    {"instruction_id": instruction_id},
                    {
                        "$set": {
                            "status": PaymentStatus.CONFIRMED,
                            "confirmed_at": datetime.now(timezone.utc),
                            "confirmed_by": admin_id
                        }
                    }
                )
                
                # Update order status
                await self.orders_collection.update_one(
                    {"order_id": order["order_id"]},
                    {
                        "$set": {
                            "status": OrderStatus.PAYMENT_CONFIRMED,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                # Update escrow status
                await self.escrow_collection.update_one(
                    {"order_id": order["order_id"]},
                    {
                        "$set": {
                            "status": EscrowStatus.FUNDS_HELD,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                # Record transaction
                await self._record_transaction(
                    order["order_id"], TransactionType.ESCROW_DEPOSIT,
                    order["total_amount"], order["currency"],
                    order["customer_id"], "platform",
                    f"Escrow deposit for order {order['order_id']}",
                    admin_id
                )
                
                # Notify both parties
                await self._send_notification(
                    order["customer_id"], "customer", EscrowNotificationType.PAYMENT_CONFIRMED,
                    "Payment Confirmed",
                    f"Your payment for order {order['order_id']} has been confirmed. Funds are now in escrow.",
                    {"order_id": order["order_id"]}
                )
                
                await self._send_notification(
                    order["vendor_id"], "vendor", EscrowNotificationType.PAYMENT_CONFIRMED,
                    "Payment Confirmed",
                    f"Payment confirmed for order {order['order_id']}. You can now proceed with delivery.",
                    {"order_id": order["order_id"]}
                )
                
                return True, "Payment confirmed successfully"
            else:
                # Reject payment
                await self.payments_collection.update_one(
                    {"instruction_id": instruction_id},
                    {
                        "$set": {
                            "status": PaymentStatus.FAILED,
                            "updated_at": datetime.now(timezone.utc),
                            "rejection_notes": notes
                        }
                    }
                )
                
                # Update order status back to pending payment
                await self.orders_collection.update_one(
                    {"order_id": order["order_id"]},
                    {
                        "$set": {
                            "status": OrderStatus.PENDING_PAYMENT,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                # Notify customer
                await self._send_notification(
                    order["customer_id"], "customer", EscrowNotificationType.PAYMENT_SUBMITTED,
                    "Payment Rejected",
                    f"Payment for order {order['order_id']} was rejected. Reason: {notes}",
                    {"order_id": order["order_id"], "reason": notes}
                )
                
                return True, f"Payment rejected: {notes}"
                
        except Exception as e:
            logger.error(f"Failed to confirm payment: {e}")
            return False, "Failed to process payment confirmation"
    
    # ===== ORDER FULFILLMENT =====
    
    async def mark_order_delivered(self, vendor_id: str, order_id: str, delivery_notes: str = "") -> Tuple[bool, Optional[str]]:
        """Vendor marks order as delivered"""
        try:
            # Get order
            order = await self.orders_collection.find_one({"order_id": order_id, "vendor_id": vendor_id})
            if not order:
                return False, "Order not found or unauthorized"
            
            if order["status"] != OrderStatus.PAYMENT_CONFIRMED.value:
                return False, f"Order must be in payment confirmed status. Current status: {order['status']}"
            
            # Update order status
            await self.orders_collection.update_one(
                {"order_id": order_id},
                {
                    "$set": {
                        "status": OrderStatus.DELIVERED,
                        "delivered_at": datetime.now(timezone.utc),
                        "delivery_notes": delivery_notes,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Notify customer
            await self._send_notification(
                order["customer_id"], "customer", EscrowNotificationType.ORDER_DELIVERED,
                "Order Delivered",
                f"Your order {order_id} has been marked as delivered. Please confirm receipt to release funds.",
                {"order_id": order_id, "delivery_notes": delivery_notes}
            )
            
            logger.info(f"Order marked as delivered: {order_id}")
            
            return True, "Order marked as delivered successfully"
            
        except Exception as e:
            logger.error(f"Failed to mark order as delivered: {e}")
            return False, "Failed to mark order as delivered"
    
    async def confirm_order_receipt(self, customer_id: str, order_id: str, satisfaction_rating: int = 5) -> Tuple[bool, Optional[str]]:
        """Customer confirms receipt and satisfaction"""
        try:
            # Get order
            order = await self.orders_collection.find_one({"order_id": order_id, "customer_id": customer_id})
            if not order:
                return False, "Order not found or unauthorized"
            
            if order["status"] != OrderStatus.DELIVERED.value:
                return False, f"Order must be delivered first. Current status: {order['status']}"
            
            # Update order status
            await self.orders_collection.update_one(
                {"order_id": order_id},
                {
                    "$set": {
                        "status": OrderStatus.COMPLETED,
                        "completed_at": datetime.now(timezone.utc),
                        "satisfaction_rating": satisfaction_rating,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Release escrow funds
            success, message = await self._release_escrow_funds(order_id, "customer_confirmation")
            if not success:
                return False, f"Failed to release funds: {message}"
            
            return True, "Order completed and funds released successfully"
            
        except Exception as e:
            logger.error(f"Failed to confirm order receipt: {e}")
            return False, "Failed to confirm order receipt"
    
    # ===== ESCROW MANAGEMENT =====
    
    async def _release_escrow_funds(self, order_id: str, release_method: str, released_by: str = "system") -> Tuple[bool, Optional[str]]:
        """Release escrow funds to vendor"""
        try:
            # Get escrow account
            escrow = await self.escrow_collection.find_one({"order_id": order_id})
            if not escrow:
                return False, "Escrow account not found"
            
            if escrow["status"] != EscrowStatus.FUNDS_HELD.value:
                return False, f"Funds not in held status. Current status: {escrow['status']}"
            
            # Update escrow status
            await self.escrow_collection.update_one(
                {"escrow_id": escrow["escrow_id"]},
                {
                    "$set": {
                        "status": EscrowStatus.RELEASED_TO_VENDOR,
                        "released_at": datetime.now(timezone.utc),
                        "released_by": released_by,
                        "release_method": release_method
                    }
                }
            )
            
            # Record vendor payout transaction
            await self._record_transaction(
                order_id, TransactionType.ESCROW_RELEASE,
                escrow["vendor_amount"], escrow["currency"],
                "platform", escrow["vendor_id"],
                f"Escrow release for order {order_id}",
                released_by
            )
            
            # Record platform fee transaction
            await self._record_transaction(
                order_id, TransactionType.PLATFORM_FEE,
                escrow["platform_fee"], escrow["currency"],
                "platform", "platform",
                f"Platform fee for order {order_id}",
                released_by
            )
            
            # Notify vendor
            await self._send_notification(
                escrow["vendor_id"], "vendor", EscrowNotificationType.FUNDS_RELEASED,
                "Funds Released",
                f"Escrow funds for order {order_id} have been released to your account.",
                {"order_id": order_id, "amount": escrow["vendor_amount"], "currency": escrow["currency"]}
            )
            
            logger.info(f"Escrow funds released for order: {order_id}")
            
            return True, "Funds released successfully"
            
        except Exception as e:
            logger.error(f"Failed to release escrow funds: {e}")
            return False, "Failed to release escrow funds"
    
    async def request_extension(self, user_id: str, order_id: str, extension_data: EscrowExtensionRequest) -> Tuple[bool, Optional[str]]:
        """Request extension of auto-release date"""
        try:
            # Get order
            order = await self.orders_collection.find_one({"order_id": order_id})
            if not order:
                return False, "Order not found"
            
            # Verify requester is part of the order
            if user_id not in [order["customer_id"], order["vendor_id"]]:
                return False, "Unauthorized to request extension"
            
            # Get escrow account
            escrow = await self.escrow_collection.find_one({"order_id": order_id})
            if not escrow or escrow["status"] != EscrowStatus.FUNDS_HELD.value:
                return False, "Escrow not in held status"
            
            # Check if extension is within limits
            if extension_data.extension_days > self.max_extension_days:
                return False, f"Maximum extension is {self.max_extension_days} days"
            
            # Add extension request
            extension_dict = extension_data.dict()
            extension_dict["order_id"] = order_id
            
            await self.escrow_collection.update_one(
                {"escrow_id": escrow["escrow_id"]},
                {
                    "$push": {"extension_requests": extension_dict}
                }
            )
            
            # Determine other party for notification
            other_party = order["vendor_id"] if user_id == order["customer_id"] else order["customer_id"]
            other_party_type = "vendor" if user_id == order["customer_id"] else "customer"
            
            # Notify other party
            await self._send_notification(
                other_party, other_party_type, EscrowNotificationType.EXTENSION_REQUESTED,
                "Extension Requested",
                f"Extension of {extension_data.extension_days} days requested for order {order_id}. Reason: {extension_data.reason}",
                {"order_id": order_id, "extension_days": extension_data.extension_days}
            )
            
            return True, "Extension request submitted successfully"
            
        except Exception as e:
            logger.error(f"Failed to request extension: {e}")
            return False, "Failed to request extension"
    
    # ===== DISPUTE MANAGEMENT =====
    
    async def create_dispute(self, customer_id: str, dispute_data: DisputeCreate) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Customer creates a dispute"""
        try:
            # Get order
            order = await self.orders_collection.find_one({"order_id": dispute_data.order_id})
            if not order or order["customer_id"] != customer_id:
                return False, None, "Order not found or unauthorized"
            
            # Check if dispute already exists
            existing_dispute = await self.disputes_collection.find_one({"order_id": dispute_data.order_id})
            if existing_dispute:
                return False, None, "Dispute already exists for this order"
            
            # Generate dispute ID
            dispute_id = f"DIS-{uuid.uuid4().hex[:10].upper()}"
            
            # Create dispute
            dispute = Dispute(
                dispute_id=dispute_id,
                order_id=dispute_data.order_id,
                customer_id=customer_id,
                vendor_id=order["vendor_id"],
                reason=dispute_data.reason,
                evidence_description=dispute_data.evidence_description,
                evidence_files=dispute_data.evidence_files,
                requested_outcome=dispute_data.requested_outcome,
                status=DisputeStatus.OPEN,
                priority=self._calculate_dispute_priority(dispute_data, order),
                auto_resolution_eligible=self._check_auto_resolution_eligibility(dispute_data, order),
                created_at=datetime.now(timezone.utc)
            )
            
            # Save dispute
            dispute_dict = dispute.dict()
            await self.disputes_collection.insert_one(dispute_dict)
            
            # Update order status
            await self.orders_collection.update_one(
                {"order_id": dispute_data.order_id},
                {
                    "$set": {
                        "status": OrderStatus.DISPUTED,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Update escrow status
            await self.escrow_collection.update_one(
                {"order_id": dispute_data.order_id},
                {
                    "$set": {
                        "status": EscrowStatus.DISPUTED,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Notify vendor
            await self._send_notification(
                order["vendor_id"], "vendor", EscrowNotificationType.DISPUTE_CREATED,
                "Dispute Created",
                f"A dispute has been created for order {dispute_data.order_id}. Please provide your response.",
                {"order_id": dispute_data.order_id, "dispute_id": dispute_id}
            )
            
            logger.info(f"Dispute created: {dispute_id}")
            
            return True, dispute_dict, None
            
        except Exception as e:
            logger.error(f"Failed to create dispute: {e}")
            return False, None, "Failed to create dispute"
    
    def _calculate_dispute_priority(self, dispute_data: DisputeCreate, order: Dict) -> int:
        """Calculate dispute priority (1-5)"""
        priority = 1
        
        # High value orders get higher priority
        if order["total_amount"] > 1000:
            priority += 1
        if order["total_amount"] > 5000:
            priority += 1
        
        # Certain dispute reasons get higher priority
        high_priority_reasons = ["fraud", "scam", "non_delivery", "damaged_goods"]
        if any(reason in dispute_data.reason.lower() for reason in high_priority_reasons):
            priority += 2
        
        return min(priority, 5)
    
    def _check_auto_resolution_eligibility(self, dispute_data: DisputeCreate, order: Dict) -> bool:
        """Check if dispute is eligible for auto resolution"""
        # Simple auto-resolution rules
        auto_resolution_reasons = ["late_delivery", "minor_damage"]
        return any(reason in dispute_data.reason.lower() for reason in auto_resolution_reasons)
    
    # ===== UTILITY METHODS =====
    
    async def _record_transaction(self, order_id: str, transaction_type: TransactionType, 
                                amount: float, currency: str, from_party: str, to_party: str,
                                description: str, processed_by: str = None):
        """Record a transaction"""
        transaction = Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
            order_id=order_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            from_party=from_party,
            to_party=to_party,
            description=description,
            processed_by=processed_by,
            created_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc)
        )
        
        await self.transactions_collection.insert_one(transaction.dict())
    
    async def _send_notification(self, recipient_id: str, recipient_type: str, 
                               notification_type: EscrowNotificationType, title: str, 
                               message: str, data: Dict[str, Any] = None):
        """Send notification to user"""
        notification = EscrowNotification(
            notification_id=str(uuid.uuid4()),
            order_id=data.get("order_id", "") if data else "",
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
            created_at=datetime.now(timezone.utc)
        )
        
        await self.notifications_collection.insert_one(notification.dict())
    
    # ===== QUERY METHODS =====
    
    async def get_order(self, order_id: str, user_id: str = None) -> Optional[Dict]:
        """Get order by ID"""
        query = {"order_id": order_id}
        if user_id:
            query["$or"] = [{"customer_id": user_id}, {"vendor_id": user_id}]
        
        order = await self.orders_collection.find_one(query)
        if order:
            order.pop("_id", None)
        return order
    
    async def get_user_orders(self, user_id: str, role: str = "customer", limit: int = 50) -> List[Dict]:
        """Get orders for a user"""
        field = "customer_id" if role == "customer" else "vendor_id"
        
        cursor = self.orders_collection.find({field: user_id}).sort("created_at", -1).limit(limit)
        orders = await cursor.to_list(length=None)
        
        for order in orders:
            order.pop("_id", None)
        
        return orders
    
    async def get_pending_payment_confirmations(self) -> List[Dict]:
        """Get payment instructions awaiting confirmation"""
        cursor = self.payments_collection.find({"status": PaymentStatus.SUBMITTED})
        payments = await cursor.to_list(length=None)
        
        for payment in payments:
            payment.pop("_id", None)
        
        return payments