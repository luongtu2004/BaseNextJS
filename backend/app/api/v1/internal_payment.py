"""Internal API — Payment Gateway Callbacks (Phase 8).

Skeleton endpoints cho VNPay/MoMo/ZaloPay IPN callbacks.
Bảo mật bằng signature verification (placeholder — cần credentials thật).

Endpoints:
  POST   /internal/payments/vnpay/callback
  POST   /internal/payments/momo/callback
  POST   /internal/payments/zalopay/callback
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.payment_service import PaymentService
from app.services.vnpay_service import VNPAYService

import json
from app.core.config import get_settings
from app.services.momo_service import MomoService
from app.services.zalopay_service import ZaloPayService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/payments", tags=["Internal / Payment Callbacks"])


@router.get(
    "/vnpay/callback",
    status_code=status.HTTP_200_OK,
    summary="VNPay IPN callback",
    description="Nhận và xử lý callback từ VNPay sau khi thanh toán. Trả về mã lỗi theo chuẩn VNPAY IPN.",
)
async def vnpay_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """VNPay IPN callback handler.

    Args:
        request: HTTP request chứa callback data (query string).
        db: Async DB session.

    Returns:
        Dict theo format VNPay IPN response. {"RspCode": "00", "Message": "Confirm Success"}
    """
    query_params = dict(request.query_params)
    safe_log = {k: v for k, v in query_params.items() if k != "vnp_SecureHash"}
    logger.info("[PAYMENT] VNPay callback received - data=%s", safe_log)

    is_valid = VNPAYService.validate_callback(query_params)
    if not is_valid:
        logger.warning("[PAYMENT] VNPay signature validation failed")
        return {"RspCode": "97", "Message": "Invalid Checksum"}

    vnp_response_code = query_params.get("vnp_ResponseCode")
    vnp_txn_ref = query_params.get("vnp_TxnRef")
    gateway_ref = query_params.get("vnp_TransactionNo")

    if not vnp_txn_ref:
        return {"RspCode": "99", "Message": "Unknown error"}

    try:
        txn_uuid = uuid.UUID(vnp_txn_ref)
        
        if vnp_response_code == "00":
            # Giao dịch thành công
            await PaymentService.complete_wallet_topup(db, txn_uuid, gateway_ref)
            await db.commit()  # explicitly commit the flush from complete_wallet_topup
        else:
            # Giao dịch thất bại / User huỷ
            # Ở môi trường thực tế, tuỳ bussiness có thay đổi status của WalletTransaction thành 'failed' không
            logger.info("[PAYMENT] VNPay transaction failed or cancelled - code=%s", vnp_response_code)

    except Exception as e:
        await db.rollback()
        logger.error("[PAYMENT] Error processing VNPay callback: %s", str(e))
        # Nếu đã completed rồi, VNPAY yêu cầu trả RspCode 02 (Order already confirmed) 
        # Tạm thời trả 00 để tắt thông báo loop từ sandbox
        if "already completed" in str(e).lower() or "already confirmed" in str(e).lower():
             return {"RspCode": "02", "Message": "Order already confirmed"}
        return {"RspCode": "99", "Message": "Unknown error"}

    return {"RspCode": "00", "Message": "Confirm Success"}


@router.post(
    "/momo/callback",
    status_code=status.HTTP_200_OK,
    summary="MoMo IPN callback",
    description="Nhận và xử lý callback từ MoMo. Xác thực bằng chữ ký SHA256.",
)
async def momo_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """MoMo IPN callback handler.

    Args:
        request: HTTP request chứa callback data.
        db: Async DB session.

    Returns:
        Dict theo format MoMo IPN response.
    """
    body = await request.json()
    safe_log = {k: v for k, v in body.items() if k != "signature"}
    logger.info("[PAYMENT] MoMo callback received - data=%s", safe_log)

    settings = get_settings()
    is_valid = MomoService.validate_callback(body, settings.momo_secret_key)
    if not is_valid:
        logger.warning("[PAYMENT] MoMo signature validation failed")
        return {"resultCode": 99}

    result_code = body.get("resultCode")
    order_id = body.get("orderId")
    trans_id = body.get("transId")

    if not order_id:
        return {"resultCode": 99}

    try:
        txn_uuid = uuid.UUID(order_id)
        if result_code == 0:
            await PaymentService.complete_wallet_topup(db, txn_uuid, str(trans_id))
            await db.commit()
    except Exception as e:
        await db.rollback()
        error_msg = str(e).lower()
        if "already completed" in error_msg:
            logger.info("[PAYMENT] MoMo callback: transaction already completed. Returning 0.")
            return {"resultCode": 0}

        logger.error("[PAYMENT] Error processing MoMo callback: %s", str(e))
        return {"resultCode": 99}

    return {"resultCode": 0}


@router.post(
    "/zalopay/callback",
    status_code=status.HTTP_200_OK,
    summary="ZaloPay callback",
    description="Nhận và xử lý callback từ ZaloPay. Xác thực bằng HMAC SHA256.",
)
async def zalopay_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int | str]:
    """ZaloPay callback handler.

    Args:
        request: HTTP request chứa callback data.
        db: Async DB session.

    Returns:
        Dict theo format ZaloPay callback response.
    """
    body = await request.json()
    safe_log = {k: v for k, v in body.items() if k != "mac"}
    logger.info("[PAYMENT] ZaloPay callback received - data=%s", safe_log)

    settings = get_settings()
    data_str = body.get("data", "")
    request_mac = body.get("mac", "")

    is_valid = ZaloPayService.validate_callback(data_str, request_mac, settings.zalopay_key2)
    if not is_valid:
        logger.warning("[PAYMENT] ZaloPay mac validation failed")
        return {"return_code": -1, "return_message": "mac not match"}

    try:
        data_json = json.loads(data_str)
        app_trans_id = data_json.get("app_trans_id")
        zp_trans_id = data_json.get("zp_trans_id")

        if not app_trans_id:
             return {"return_code": 0, "return_message": "unknown error"}

        txn_uuid = uuid.UUID(app_trans_id)

        # ZaloPay callback assumes success
        await PaymentService.complete_wallet_topup(db, txn_uuid, str(zp_trans_id))
        await db.commit()

    except Exception as e:
        await db.rollback()
        error_msg = str(e).lower()
        if "already completed" in error_msg:
            logger.info("[PAYMENT] ZaloPay callback: transaction already completed. Returning 1.")
            return {"return_code": 1, "return_message": "already completed"}

        logger.error("[PAYMENT] Error processing ZaloPay callback: %s", str(e))
        return {"return_code": 0, "return_message": str(e)}

    return {"return_code": 1, "return_message": "success"}
