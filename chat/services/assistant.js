import mongoDb from "../mongoDb.js";
import { request } from "../request.js";
import env from "../env.js";

const filterTheSame = (originArray) => {
    const res = originArray.filter((item, index, self) => {
        return self.indexOf(item) === index;
    });
    return Array.from(res);
};

export const getSocketIdOfListUserActive = async (listUserId) => {
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

export const getListInfoUser = async ({ listUserId, displayAvatar, token }) => {
    const res = await request.post(
        "/chat/list-info-user",
        {
            listUserId,
            displayAvatar,
        },
        {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }
    );
    return res.data;
};

export const getUserIdFromToken = async (token) => {
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

export const createLinkImage = (imageName) => {
    return `${env.AWS_IMAGE_URL}/${imageName}`;
};
