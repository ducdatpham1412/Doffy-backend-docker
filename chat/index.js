import { createServer } from "http";
import { Server } from "socket.io";
import { SOCKET_EVENT } from "./enum.js";
import mongoDb from "./mongoDb.js";
import { getSocketIdOfListUserActive } from "./services/assistant.js";
import { getMyListChatTagsAndMyId } from "./services/authentication.js";
import { addComment } from "./services/bubble.js";
import {
    changeGroupName,
    getLatestMessage,
    handleAgreePublicChat,
    handleChangeChatColor,
    handleRequestPublicChat,
    handleStartNewChatTag,
} from "./services/chatTag.js";
import {
    handleSendMessage,
    handleSendMessageEnjoy,
} from "./services/message.js";
import Static from "./static.js";

const httpServer = createServer();
const io = new Server(httpServer, {
    pingTimeout: 60000,
    pingInterval: 25000,
});

const enjoyModeRoom = "enjoy-mode-room";

io.on("connection", (socket) => {
    console.log("\n\nSocket connect with: ", socket.id);

    /**
     * Authenticate
     */
    socket.on(SOCKET_EVENT.authenticate, async (params) => {
        try {
            // user have account
            if (params?.token) {
                const { listMyChatTag, myId } = await getMyListChatTagsAndMyId(
                    params.token
                );
                // save to user active
                await mongoDb
                    .collection("userActive")
                    .deleteMany({ userId: myId });
                await mongoDb.collection("userActive").insertOne({
                    userId: myId,
                    socketId: socket.id,
                });
                Static.addUserActive({
                    userId: myId,
                    socketId: socket.id,
                });
                // join all room of chat tag have in
                listMyChatTag.forEach((item) => {
                    socket.join(String(item._id));
                });
            }

            // use enjoy mode
            else if (params?.myId) {
                await mongoDb
                    .collection("userActive")
                    .deleteMany({ userId: params.myId });
                await mongoDb.collection("userActive").insertOne({
                    userId: params.myId,
                    socketId: socket.id,
                });
                Static.addUserActive({
                    userId: params.myId,
                    socketId: socket.id,
                });
                // join room for only enjoy user
                socket.join(enjoyModeRoom);
            }
        } catch (err) {
            console.log("Error authenticate: ", socket.id);
            socket.emit(SOCKET_EVENT.unauthorized);
        }
    });

    socket.on(SOCKET_EVENT.appActive, () => {
        Static.putBackActive(socket.id);
    });
    socket.on(SOCKET_EVENT.appBackground, () => {
        Static.putInBackground(socket.id);
    });

    /**
     * Bubble
     */
    socket.on(SOCKET_EVENT.addComment, async (params) => {
        try {
            const res = await addComment(params);
            io.to(params.bubbleId).emit(SOCKET_EVENT.addComment, res);
        } catch (err) {
            console.log("Err adding comment: ", socket.id);
        }
    });

    /**
     * ChatTag
     */
    socket.on(SOCKET_EVENT.createChatTag, async (params) => {
        try {
            const res = await handleStartNewChatTag(params);
            // If chat tag existed, only send message to user
            if (res.isChatTagExisted) {
                io.to(res.response.chatTag).emit(
                    SOCKET_EVENT.message,
                    res.response
                );
                return;
            }

            const listSocketId = await getSocketIdOfListUserActive(
                res.response.listUser.map((item) => item.id)
            );
            listSocketId.forEach((socketId) => {
                io.to(socketId).emit(SOCKET_EVENT.createChatTag, res.response);
            });
        } catch (err) {
            console.log("Error when create chat tag: ", socket.id);
        }
    });
    // after receive socket "createChatTag" in client, join room of that chat tag
    socket.on(SOCKET_EVENT.joinRoom, (chatTagId) => {
        console.log("join room: ", chatTagId);
        socket.join(chatTagId);
    });

    socket.on(SOCKET_EVENT.seenMessage, async (params) => {
        try {
            let res = undefined;
            // enjoy mode
            if (params?.isEnjoy) {
                res = {
                    chatTagId: params.chatTagId,
                    userSeen: params.myId,
                };
            }
            // user have account
            else {
                res = await getLatestMessage(params);
            }
            io.to(params.chatTagId).emit(SOCKET_EVENT.seenMessage, res);
        } catch (err) {
            console.log("Error seen message: ", socket.id);
        }
    });

    socket.on(SOCKET_EVENT.requestPublicChat, async (chatTagId) => {
        try {
            await handleRequestPublicChat(chatTagId);
            io.to(chatTagId).emit(SOCKET_EVENT.requestPublicChat, chatTagId);
        } catch (err) {
            console.log("Error request public chat: ", socket.id);
        }
    });
    socket.on(SOCKET_EVENT.agreePublicChat, async (params) => {
        try {
            const chatTagPublic = await handleAgreePublicChat(params);
            if (chatTagPublic) {
                io.to(chatTagPublic.id).emit(
                    SOCKET_EVENT.allAgreePublicChat,
                    chatTagPublic
                );
            }
        } catch (err) {
            console.log("Error agree public chat: ", socket.id);
        }
    });

    socket.on(SOCKET_EVENT.changeGroupName, async (params) => {
        try {
            const check = await changeGroupName(params);
            if (check) {
                io.to(params.chatTagId).emit(SOCKET_EVENT.changeGroupName, {
                    chatTagId: params.chatTagId,
                    newName: params.newName,
                });
            }
        } catch (err) {
            console.log("Error change group name: ", socket.id);
        }
    });

    socket.on(SOCKET_EVENT.changeChatColor, async (params) => {
        try {
            const check = await handleChangeChatColor({
                socketId: socket.id,
                ...params,
            });
            if (check) {
                io.to(params.chatTagId).emit(SOCKET_EVENT.changeChatColor, {
                    chatTagId: params.chatTagId,
                    newColor: params.newColor,
                });
            }
        } catch (err) {
            console.log("Error change chat color: ", socket.id);
        }
    });

    /**
     * Block, stop conversation
     */
    socket.on(SOCKET_EVENT.isBlocked, async ({ listUserId, listChatTagId }) => {
        try {
            const listSocketId = await getSocketIdOfListUserActive(listUserId);
            listSocketId.forEach((item) => {
                io.to(item).emit(SOCKET_EVENT.isBlocked, listChatTagId);
            });
        } catch (err) {
            console.log("Error block: ", socket.id);
        }
    });
    socket.on(SOCKET_EVENT.unBlocked, async ({ listUserId, listChatTagId }) => {
        try {
            const listSocketId = await getSocketIdOfListUserActive(listUserId);
            listSocketId.forEach((item) => {
                io.to(item).emit(SOCKET_EVENT.unBlocked, listChatTagId);
            });
        } catch (err) {
            console.log("Error un-block: ", socket.id);
        }
    });

    socket.on(SOCKET_EVENT.stopConversation, (chatTagId) => {
        io.to(chatTagId).emit(SOCKET_EVENT.stopConversation, chatTagId);
    });
    socket.on(SOCKET_EVENT.openConversation, (chatTagId) => {
        io.to(chatTagId).emit(SOCKET_EVENT.openConversation, chatTagId);
    });

    /**
     * Message
     */
    socket.on(SOCKET_EVENT.message, async (params) => {
        const res = await handleSendMessage(params);
        io.to(res.chatTag).emit(SOCKET_EVENT.message, res);
    });
    socket.on(SOCKET_EVENT.messageEnjoy, (params) => {
        const res = handleSendMessageEnjoy(params);
        io.to(res.chatTag).emit(SOCKET_EVENT.messageEnjoy, res);
    });
    socket.on(SOCKET_EVENT.deleteMessage, (params) => {
        const { chatTagId, messageId } = params;
        io.to(chatTagId).emit(SOCKET_EVENT.deleteMessage, params);
    });
    socket.on(SOCKET_EVENT.typing, (params) => {
        const { chatTagId, userId } = params;
        io.to(chatTagId).emit(SOCKET_EVENT.typing, params);
    });
    socket.on(SOCKET_EVENT.unTyping, (params) => {
        const { chatTagId, userId } = params;
        io.to(chatTagId).emit(SOCKET_EVENT.unTyping, params);
    });

    /**
     * Disconnect
     */
    socket.on("disconnect", async (reason) => {
        try {
            console.log(`Disconnected: ${socket.id}\nReason: `, reason);

            await mongoDb
                .collection("userActive")
                .findOneAndDelete({ socketId: socket.id });
            /**
             * Leave room - you don't need because socketIO will do this for you
             */
            Static.removeUserActive(socket.id);
        } catch (err) {
            console.log("Error disconnect: ", socket.id);
        }
    });
});

httpServer.listen(3000);
