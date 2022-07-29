import { MongoClient } from "mongodb";
import isEqual from "react-fast-compare";

const uri = `mongodb://ducdatpham:ducdat123@127.0.0.1:27017/?authSource=admin&readPreference=primary&serverSelectionTimeoutMS=2000&appname=MongoDB%20Compass&directConnection=true&ssl=false`;

const client = new MongoClient(uri);
client.connect();
const mongoDb = client.db("doffy");

const query = async () => {
    const listOldConversation = await (
        await mongoDb.collection("__old_chat_conversation").find()
    ).toArray();

    const newListConversations: Array<any> = [];

    listOldConversation.forEach((conversation) => {
        if (conversation.type !== 2) {
            const checkHadBefore = newListConversations.find((item) =>
                isEqual(item.list_users, conversation.listUser.sort())
            );

            if (checkHadBefore) {
                newListConversations.every((item) => {
                    if (
                        isEqual(item.list_users, conversation.listUser.sort())
                    ) {
                        item.total_messages += conversation.listMessages.length;
                        item.list_messages = item.list_messages.concat(
                            conversation.listMessages
                        );
                        return false;
                    }
                    return true;
                });
            } else {
                const userData: any = {};
                for (const [key] of Object.entries(
                    conversation.userSeenMessage
                )) {
                    userData[key] = {
                        created: "start",
                        modified: conversation.updateTime,
                    };
                }
                const newConversation = {
                    _id: conversation._id,
                    list_users: conversation.listUser.sort(),
                    conversation_name: "",
                    conversation_image: conversation?.image,
                    color: conversation.color,
                    created:
                        conversation?.createdTime ||
                        conversation?.updateTime ||
                        new Date(),
                    modified: conversation?.updateTime || new Date(),
                    user_data: userData,
                    total_messages: conversation.listMessages.length,
                    latest_message: "",
                    status: 1,
                    list_messages: conversation.listMessages || [],
                };

                newListConversations.push(newConversation);
            }
        }
    });

    newListConversations.forEach(async (conversation) => {
        const insertConversation = {
            _id: conversation._id,
            list_users: conversation.list_users,
            conversation_name: conversation.conversation_name,
            conversation_image: conversation.conversation_image,
            color: conversation.color,
            created: conversation.created,
            modified: conversation.modified,
            user_data: conversation.user_data,
            total_messages: conversation.total_messages,
            latest_message: conversation.latest_message,
            status: conversation.status,
        };
        await mongoDb
            .collection("chat_conversation")
            .insertOne(insertConversation);

        conversation.list_messages.forEach(async (message: any) => {
            const newMessage = {
                _id: message._id,
                type: message.type,
                content: message.content,
                creator: message.senderId,
                created: message.createdTime,
                conversation_id: String(conversation._id),
                status: 1,
            };
            await mongoDb.collection("chat_message").insertOne(newMessage);
        });
    });
};

query();
