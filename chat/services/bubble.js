import mongoDb from "../mongoDb.js";

export const increaseAndGetNumberBubbles = async () => {
    const temp = await mongoDb.collection("numberBubbles").findOneAndUpdate(
        {},
        {
            $inc: {
                number: 1,
            },
        }
    );
    return temp.value.number + 1;
};

export const getListSocketIdOfUserEnjoy = async () => {
    const res = await mongoDb
        .collection("userActive")
        .find({
            userId: {
                $regex: "__",
            },
        })
        .toArray();
    return res.map((item) => item.socketId);
};
