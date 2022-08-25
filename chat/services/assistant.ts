import { GENDER, STATUS } from "../enum";
import env from "../env";
import {
    TypeGetListInfoUserRequest,
    TypeGetListInfoUserResponse,
} from "../interface/chatTag";
import mongoDb from "../mongoDb";
import { request } from "../request";

const filterTheSame = (originArray: Array<any>) => {
    const res = originArray.filter((item, index, self) => {
        return self.indexOf(item) === index;
    });
    return Array.from(res);
};

export const getSocketIdOfListUserActive = async (
    listUserId: Array<number>
) => {
    const result = [];
    const listUniqueId = filterTheSame(listUserId);
    for (let i = 0; i < listUniqueId.length; i++) {
        const check = await mongoDb
            .collection("user_active")
            .findOne({ user_id: listUniqueId[i] });
        if (check) result.push(check.socket_id);
    }
    return result;
};

export const getSocketIdOfUserId = async (userId: number) => {
    const result = await mongoDb.collection("user_active").findOne({
        user_id: userId,
    });
    return result?.socket_id || "";
};

export const getListInfoUser = async (
    params: TypeGetListInfoUserRequest
): Promise<Array<TypeGetListInfoUserResponse>> => {
    const res = await request.post(
        "/chat/list-info-user",
        {
            listUserId: params.listUserId,
        },
        {
            headers: {
                Authorization: `Bearer ${params.token}`,
            },
        }
    );
    return res.data;
};

export const getUserIdFromToken = async (token: string) => {
    const res = await request.get("auth/verify-token", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
    return res.data;
};

export const getDateTimeNow = () => {
    return new Date();
};

export const createLinkImage = (imageName: string) => {
    return `${env.AWS_IMAGE_URL}/${imageName}`;
};

export const choosePrivateAvatar = (gender: number) => {
    switch (gender) {
        case GENDER.male:
            return createLinkImage("__admin_girl.png");
        case GENDER.female:
            return createLinkImage("__admin_boy.png");
        case GENDER.notToSay:
            return createLinkImage("__admin_lgbt.png");
        default:
            return createLinkImage("__admin_girl.png");
    }
};

/**
 * User active
 */

export const addUserActive = async (params: {
    userId: number;
    socketId: string;
}) => {
    await mongoDb.collection("user_active").deleteMany({
        user_id: params.userId,
    });
    await mongoDb.collection("user_active").insertOne({
        user_id: params.userId,
        socket_id: params.socketId,
        status: STATUS.active,
    });
};

export const putUserInBackground = async (socketId: string) => {
    await mongoDb.collection("user_active").findOneAndUpdate(
        {
            socket_id: socketId,
        },
        {
            $set: {
                status: STATUS.notActive,
            },
        }
    );
};

export const putBackUserActive = async (socketId: string) => {
    await mongoDb.collection("user_active").findOneAndUpdate(
        {
            socket_id: socketId,
        },
        {
            $set: {
                status: STATUS.active,
            },
        }
    );
};

export const checkUserActive = async (userId: number) => {
    const check = await mongoDb.collection("user_active").findOne({
        user_id: userId,
        status: STATUS.active,
    });
    return !!check;
};

export const removerUserActive = async (socketId: string) => {
    await mongoDb.collection("user_active").deleteOne({
        socket_id: socketId,
    });
};
