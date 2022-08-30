import { MongoClient, ObjectId } from "mongodb";

const uri = `mongodb://ducdatpham:ducdat123@127.0.0.1:27017/?authSource=admin&readPreference=primary&serverSelectionTimeoutMS=2000&appname=MongoDB%20Compass&directConnection=true&ssl=false`;

const client = new MongoClient(uri);
client.connect();
const mongoDb = client.db("doffy");

const choosingType = (type: number) => {
    if (type === 0) return 0;
    if (type === 1) return 2;
    if (type === 2) return 3;
    if (type === 3) return 4;
    if (type === 4) return 1;
};

const query = async () => {
    const listNotifications = await mongoDb
        .collection("__old_notification")
        .find()
        .toArray();

    listNotifications.forEach((notification) => {
        notification.list.forEach(async (item: any) => {
            const insertNotification: any = {
                _id: new ObjectId(item.id),
                type: choosingType(item.type),
                user_id: notification.userId,
            };
            if (item.bubbleId) {
                insertNotification.post_id = item.bubbleId;
            }
            insertNotification.creator = item.creatorId;
            insertNotification.created = insertNotification._id.getTimestamp();
            insertNotification.status = item.hadRead ? 2 : 1;

            await mongoDb
                .collection("notification")
                .insertOne(insertNotification);
        });
    });
};

query();
