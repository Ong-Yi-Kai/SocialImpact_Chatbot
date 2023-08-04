from sentence_transformers import SentenceTransformer
import pinecone
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.prompts import ( SystemMessagePromptTemplate, HumanMessagePromptTemplate,
                                ChatPromptTemplate, MessagesPlaceholder )
from langchain.llms import OpenAI
from streamlit_chat import message
from src.utils import *


# Frontend BS
st.set_page_config(page_title="PLastic GPT", page_icon="♻", layout="wide")

with st.sidebar:
    st.header("Plastics Social Impact Chatbot")
    st.markdown("# About 🙌")
    st.markdown(
        "Type a chemical compound name and the chatbot would return cases related to that compound"
        )

# Credentials /  keys
# os.environ['OPENAI_API_KEY'] = st.secrets.openai.api_key
# openai.api_key = st.secrets.openai.api_key
#
# pinecone.init(api_key=st.secrets.pinecone.api_key, environment=st.secrets.pinecone.env)
# index = pinecone.Index(st.secrets.pinecone.index_name)
#
# llm = OpenAI(model_name="text-davinci-003", openai_api_key=st.secrets.openai.api_key)         # model used to come up with response
# model = SentenceTransformer('all-MiniLM-L6-v2')     # model used to find matches and to encode initial pdfs
openai.api_key = "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"

pinecone.init(api_key="232e5f68-2d67-4bc2-9ab4-6dd3855f6e49",
              environment="us-west4-gcp")
index = pinecone.Index("plastic-cases-index")

llm = OpenAI(model_name="text-davinci-002", openai_api_key=openai.api_key)         # model used to come up with response
model = SentenceTransformer('all-MiniLM-L6-v2')     # model used to find matches and to encode initial pdfs



# conversation state to store history of conservation
if 'responses' not in st.session_state:
    st.session_state['responses'] = ["Which Chemical Compound would you like to know more about?"]

if 'requests' not in st.session_state:
    st.session_state['requests'] = []

if 'contexts' not in st.session_state:
    st.session_state['contexts'] = ["None"]

if 'buffer_memory' not in st.session_state:
    st.session_state.buffer_memory=ConversationBufferWindowMemory(k=3,return_messages=True)

print(st.session_state.keys())

system_msg_template = SystemMessagePromptTemplate.from_template(template="""Answer the question as truthfully as possible using the provided context,
and if the answer is not contained within the text below, say 'I don't know'""")

human_msg_template = HumanMessagePromptTemplate.from_template(template="{input}")

prompt_template = ChatPromptTemplate.from_messages([system_msg_template, MessagesPlaceholder(variable_name="history"), human_msg_template])

conversation = ConversationChain(memory=st.session_state.buffer_memory,
                                 prompt=prompt_template, llm=llm, verbose=True)

# creating user interface
st.title("Plastic Social Impact Chatbot")
# container for chat history
response_container = st.container()
# container for text box
textcontainer = st.container()


with textcontainer:
    compound = st.text_input("Chemical Compound: ", key="input")
    if compound:
        with st.spinner("typing..."):
            conversation_string = get_conversation_string()
            # st.code(conversation_string)
            # Make our QA-Model smarter via refining Queries and finding matches with utility functions
            # refined_query = query_refiner(conversation_string, query)
            refined_query = f"Cases related to the chemical {compound}"
            st.subheader("Refined Query:")
            st.write(refined_query)
            context = find_match(refined_query, model, index)
            # print(context)
            try:
                response = conversation.predict(input=f"Context:\n {context} \n\n Query:\nSummarise the impacts related to {compound} from the court cases provided in the context in more than 100 words")
            except:
                response = "Server Error ... "

        # store the results
        st.session_state.requests.append(compound)
        st.session_state.responses.append(response)
        st.session_state.contexts.append(context)

with response_container:
    if st.session_state['responses']:

        for i in range(len(st.session_state['responses'])):
            message(f"Response:\n{st.session_state['responses'][i]}",key=str(i))
            # print context for queries
            message(f"Context:{st.session_state['contexts'][i]}", key=str(i) + '_context')
            if i < len(st.session_state['requests']):
                message(st.session_state["requests"][i], is_user=True,key=str(i)+ '_user')
