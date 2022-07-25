import mongoDb from "../mongoDb";
import { request } from "../request";
import env from "../env";
import { GENDER } from "../enum";
import {
    TypeGetListInfoUserRequest,
    TypeGetListInfoUserResponse,
} from "../interface/chatTag";

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
            .collection("userActive")
            .findOne({ userId: listUniqueId[i] });
        if (check) result.push(check.socketId);
    }
    return result;
};

export const getSocketIdOfUserId = async (userId: number) => {
    const result = await mongoDb.collection("userActive").findOne({
        userId,
    });
    return result?.socketId || "";
};

export const getListInfoUser = async (
    params: TypeGetListInfoUserRequest
): Promise<Array<TypeGetListInfoUserResponse>> => {
    const res = await request.post(
        "/chat/list-info-user",
        {
            listUserId: params.listUserId,
            displayAvatar: params.displayAvatar,
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
