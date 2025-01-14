import sys
import pathlib
import jwt
import sqlalchemy

sys.path.insert(0, f'{pathlib.Path(__file__).parents[2]}/token_service')
sys.path.insert(1, f'{pathlib.Path(__file__).parents[2]}/database')
sys.path.insert(2, f'{pathlib.Path(__file__).parents[2]}/database/fastapi_sql')
from fastapi import FastAPI, BackgroundTasks, Query, Body, HTTPException, Depends, Body, APIRouter
from dependencies import get_session, oauth2_scheme
from token_workflow import Token_dash
from token_service import create_access_token
from user_service import get_user, create_user, authenticate_user, get_current_user, delete_user, update_user
from jwt_token_service import jwt_t_service
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_service.pydantic_models import Users_pydantic, Users_pydantic_out_wrapper
from fastapi.responses import JSONResponse
from mongoDB.fastapi_mongo.user_service import user_mongo

router = APIRouter()


@router.post("/api/login", responses={404: {'description': 'User not found!'}})
async def login_for_access_token(username: str = Body(), password: str = Body(),
                                 session: AsyncSession = Depends(get_session)):
    user = await get_user(session, username)
    if not user:
        raise HTTPException(status_code=403, detail={"message": "Username or password does not match.", "data": ""})
    if not await authenticate_user(session, username, password):
        raise HTTPException(status_code=403, detail={"message": "Username or password does not match.", "data": ""})
    jwt_token = jwt_t_service.create_jwt_token(user)
    refresh_token=jwt_t_service.create_jwt_refresh_token(user)
    return {
        "detail": {"data": {"access_token": jwt_token, "token_type": "bearer",
                            "refresh_token": refresh_token, "refresh_token_type": "bearer"},
                   "message": "JWT token was created!"}}


@router.post("/api/create_user/", status_code=201, response_model=Users_pydantic_out_wrapper,
             response_model_exclude={"detail": {"data": {"password"}}})
async def new_user(user: Users_pydantic, session: AsyncSession = Depends(get_session)):
    try:
        await create_user(session, user)
        print(user)
        return {"detail": {"data": user, "message": "user was created!"}}
    except sqlalchemy.exc.IntegrityError:
        raise HTTPException(status_code=400, detail={"message": "User already exist", "data": ""})


@router.get("/api/user",status_code=200, response_model=Users_pydantic_out_wrapper,
            response_model_exclude={"detail": {"data": {"password"}}})
async def read_user(session: AsyncSession = Depends(get_session), jwt_token: str = Depends(oauth2_scheme)):
    user = await get_current_user(session, jwt_token)
    return {"detail": {"data": user.__dict__, "message": "current logged in user"}}

@router.delete("/api/user/delete",status_code=200)
async def read_user(session: AsyncSession = Depends(get_session), jwt_token: str = Depends(oauth2_scheme)):
    user_id = await get_current_user(session,jwt_token)
    await delete_user(session,user_id.id)
    return {"detail": {"data": "", "message": "user was deleted"}}

@router.put("/api/user/update",status_code=200)
async def update_username(new_username: str = Body(embed=True), session: AsyncSession = Depends(get_session)
                          ,jwt_token: str = Depends(oauth2_scheme)):
    user_id = await get_current_user(session,jwt_token)
    try:
        await update_user(session,user_id.id,new_username)
        return {"detail": {"data": "", "message": f"Username was updated. New username is {new_username}"}}
    except sqlalchemy.exc.IntegrityError:
        HTTPException(status_code=400, detail={"message": f"User with username: {new_username} already exist", "data": ""})
    except Exception:
        HTTPException(status_code=400,
                      detail={"message": "operation is not allowed", "data": ""})