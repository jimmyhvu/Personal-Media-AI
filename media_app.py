import streamlit as st

from media_engine import (
    discover_media,
    evaluate_media,
    add_review,
    load_profile,
    load_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    load_review_drafts,
    save_review_draft,
    delete_review_draft,
    get_visual,
    save_visual, 
    fetch_media_visual,
    suggest_review_candidates,
    load_media_chat,
    save_media_chat,
    clear_media_chat,
    load_media_notes,
    save_media_note,
    chat_about_media,
    extract_taste_signal_from_excerpt,
    save_manual_taste_signal,
    load_manual_taste_signals,
    remove_manual_taste_signal,
    draft_review_from_chat,
)


from media_lookup import lookup_availability, search_title

st.set_page_config(
    page_title="Personal Media AI",
    page_icon="🎬",
    layout="wide"
)

st.title("Personal Media AI")
st.caption(
    "Recommendations based on your reviews, behavior, "
    "and cross-media taste profile."
)

@st.dialog("Quick review")
def quick_review_dialog(title, media_type="Other"):

    st.write(f"**{title}**")

    rating = st.slider(
        "Rating",
        1,
        10,
        7,
        key=f"quick_rating_{title}"
    )

    thoughts = st.text_area(
        "What did you think?",
        key=f"quick_thoughts_{title}",
        height=140
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Save now",
            type="primary",
            key=f"quick_save_{title}"
        ):

            if not thoughts.strip():
                st.warning("Add at least a short reaction.")

            else:
                with st.spinner("Saving review..."):
                    add_review(
                        title,
                        media_type,
                        rating,
                        thoughts
                    )

                if "review_memory_suggestions" in st.session_state:
                    st.session_state.review_memory_suggestions = [
                        item
                        for item in st.session_state.review_memory_suggestions
                        if item.get("title", "").strip().lower()
                        != title.strip().lower()
                    ]

                dismissed = set(
                    st.session_state.get("review_memory_dismissed", [])
                )
                dismissed.add(title)
                st.session_state.review_memory_dismissed = sorted(dismissed)

                st.toast("Review saved.")
                st.rerun()

    with col2:
        if st.button(
            "Continue in Add Review",
            key=f"quick_continue_{title}"
        ):

            st.session_state.review_title = title
            st.session_state.review_type = media_type
            st.session_state.review_rating = rating
            st.session_state.review_thoughts = thoughts

            st.session_state.main_tabs = "✍️ Add Review"

            st.rerun()


TAB_NAMES = [
    "🔎 Discover",
    "🎯 Evaluate",
    "⭐ Watchlist",
    "✍️ Add Review",
    "💬 Media Chat",
    "🧠 Taste Profile"
]


if "next_tab" in st.session_state:
    st.session_state.main_tabs = st.session_state.next_tab
    del st.session_state.next_tab


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    TAB_NAMES,
    key="main_tabs",
    on_change="rerun"
)


# =====================================================
# DISCOVER
# =====================================================

with tab1:

    st.header("What are you in the mood for?")

    request = st.text_area(
        "Describe what you want",
        placeholder=(
            "Something intellectually engaging but not exhausting. "
            "Maybe international. Strong characters, some political "
            "or institutional texture. No horror."
        ),
        height=150
    )

    discover_web = st.checkbox(
        "Search the web for current information",
        value=True,
        key="discover_web_search",
        help="Useful for newly released or obscure media. May add API search charges."
    )

    if st.button(
        "Find something",
        key="discover_button",
        type="primary"
    ):

        if not request.strip():
            st.warning("Describe what you're in the mood for.")

        else:
            with st.spinner("Thinking about your taste..."):
                try:
                    st.session_state.discovery = (
                        discover_media(request, web_search=discover_web)
                    )
                except Exception as e:
                    st.error(str(e))


    if "discovery" in st.session_state:

        result = st.session_state.discovery

        st.subheader("What I think you're asking for")
        st.write(result.interpretation)

        st.subheader("Recommendations")

        for i, title in enumerate(result.recommendations):

            st.markdown(f"### {i + 1}. {title}")

            if i < len(result.why_these_fit):
                st.write(
                    "**Why it fits:**",
                    result.why_these_fit[i]
                )

            if i < len(result.cautions):
                st.write(
                    "**Possible drawback:**",
                    result.cautions[i]
                )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "⭐ Add to watchlist",
                    key=f"bookmark_{i}_{title}"
                ):


                    media_type = (
                        result.recommendation_types[i]
                        if i < len(result.recommendation_types)
                        else "Other"
                    )

                    added = add_to_watchlist(
                        title,
                        media_type
                    )


                    if added:
                        st.toast("Added to watchlist.")
                    else:
                        st.toast("Already on watchlist.")

            with col2:
                if st.button(
                    "✓ I've seen this",
                    key=f"seen_{i}_{title}"
                ):
                    quick_review_dialog(
                        title,
                        "Other"
                    )


# =====================================================
# EVALUATE
# =====================================================

with tab2:

    st.header("Evaluate something you're considering")

    title = st.text_input(
        "Title",
        key="evaluate_title"
    )

    media_type = st.selectbox(
        "Type",
        [
            "TV",
            "Movie",
            "Game",
            "Book",
            "Music",
            "Essay",
            "Other"
        ]
    )

    description = st.text_area(
        "What do you know about it?",
        placeholder=(
            "Paste a description, or explain what caught "
            "your attention."
        )
    )

    evaluate_web = st.checkbox(
        "Search the web for current information",
        value=False,
        key="evaluate_web_search",
        help="Check recent reviews, release dates and descriptions when evaluating a title."
    )

    if st.button(
        "Predict my reaction",
        key="evaluate_button",
        type="primary"
    ):

        if not title.strip():
            st.warning("Enter a title.")

        else:
            with st.spinner("Comparing with your taste..."):

                try:
                    st.session_state.evaluation = (
                        evaluate_media(
                            title,
                            media_type,
                            description,
                            web_search=evaluate_web
                        )
                    )

                except Exception as e:
                    st.error(str(e))


    if "evaluation" in st.session_state:

        result = st.session_state.evaluation

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Predicted fit",
                f"{result.fit_score}/10"
            )

        with col2:
            st.metric(
                "Confidence",
                result.confidence.title()
            )

        st.subheader("Likely positives")

        for item in result.likely_positives:
            st.write("•", item)

        st.subheader("Likely negatives")

        for item in result.likely_negatives:
            st.write("•", item)

        st.subheader("Relevant past examples")

        for item in result.relevant_past_examples:
            st.write("•", item)

        st.subheader("Prediction")

        st.write(result.verdict)

        if st.button(
            "⭐ Add to watchlist",
            key="evaluate_add_watchlist"
        ):
            added = add_to_watchlist(
                title,
                media_type,
                note="Added from Evaluate"
            )

            if added:
                st.toast("Added to watchlist.")
            else:
                st.toast("Already on watchlist.")


        if media_type in ["TV", "Movie"]:
            # lookup code

            st.subheader("Where to watch")



    try:
        availability = lookup_availability(
            title,
            media_type
        )

        if availability:

            providers = availability["providers"]

            if providers["stream"]:
                st.write(
                    "**Included with subscription:**",
                    ", ".join(providers["stream"])
                )

            if providers["free"]:
                st.write(
                    "**Free:**",
                    ", ".join(providers["free"])
                )

            if providers["ads"]:
                st.write(
                    "**Free with ads:**",
                    ", ".join(providers["ads"])
                )

            if providers["rent"]:
                st.write(
                    "**Rent:**",
                    ", ".join(providers["rent"])
                )

            if providers["buy"]:
                st.write(
                    "**Buy:**",
                    ", ".join(providers["buy"])
                )

            if not any([
                providers["stream"],
                providers["free"],
                providers["ads"],
                providers["rent"],
                providers["buy"]
            ]):
                st.info(
                    "No current US provider information found."
                )

            if providers["link"]:
                st.link_button(
                    "View availability",
                    providers["link"]
                )

            st.caption(
                "Streaming availability data via TMDB / JustWatch."
            )

        else:
            st.info("Couldn't find this title on TMDB.")

    except Exception as e:
        st.warning(
            f"Availability lookup failed: {e}"
        )

# =====================================================
# WATCHLIST
# =====================================================


with tab3:

    st.header("Watchlist")

    st.subheader("Add manually")

    manual_title = st.text_input(
        "Title",
        key="watchlist_manual_title"
    )

    manual_type = st.selectbox(
        "Type",
        [
            "TV",
            "Movie",
            "Game",
            "Book",
            "Music",
            "Essay",
            "Other"
        ],
        key="watchlist_manual_type"
    )

    manual_note = st.text_input(
        "Note",
        placeholder="Why you're interested, where you heard about it, etc."
    )

    if st.button(
        "Add to watchlist",
        type="primary",
        key="watchlist_manual_add"
    ):

        if not manual_title.strip():
            st.warning("Enter a title.")

        else:
            added = add_to_watchlist(
                manual_title,
                manual_type,
                manual_note
            )

            if added:
                st.success("Added.")
                st.rerun()
            else:
                st.info("Already on your watchlist.")

    st.divider()

    items = load_watchlist()

    if not items:
        st.info("Your watchlist is empty.")

    else:


        for index, item in enumerate(items):

            poster_url = None

            cached_visual = get_visual(
                item["title"],
                item["type"]
            )

            if item["type"] in ["Movie", "TV"]:
                try:
                    match = search_title(
                        item["title"],
                        item["type"]
                    )

                    if match and match.get("poster_path"):
                        poster_url = (
                            "https://image.tmdb.org/t/p/w342"
                            + match["poster_path"]
                        )

                except Exception:
                    pass

            if not poster_url and cached_visual:
                poster_url = cached_visual

            if poster_url:
                poster_col, info_col = st.columns(
                    [1, 4],
                    vertical_alignment="top"
                )

                with poster_col:
                    st.image(
                        poster_url,
                        width="stretch"
                    )

                with info_col:
                    st.markdown(
                        f"### {item['title']}"
                    )

                    st.caption(item["type"])

                    if item.get("note"):
                        st.write(item["note"])

            else:
                st.markdown(
                    f"### {item['title']}"
                )

                st.caption(item["type"])

                if item.get("note"):
                    st.write(item["note"])




            col1, col2, col3, col4 = st.columns(4)

            if not poster_url and item["type"] not in ["Movie", "TV"]:
                if st.button(
                    "🖼️ Fetch artwork",
                    key=f"fetch_artwork_{index}"
                ):

                    with st.spinner("Finding artwork..."):
                        image_url = fetch_media_visual(
                            item["title"],
                            item["type"]
                        )

                    if image_url:
                        save_visual(
                            item["title"],
                            item["type"],
                            image_url
                        )

                        st.rerun()

                    else:
                        st.warning(
                            "Couldn't confidently find artwork for this item."
                        )


            with col1:
                if st.button(
                    "✓ I've consumed this",
                    key=f"watch_seen_{index}"
                ):
                    quick_review_dialog(
                        item["title"],
                        item["type"]
                    )

            with col2:
                if st.button(
                    "Remove",
                    key=f"watch_remove_{index}"
                ):

                    remove_from_watchlist(
                        item["title"],
                        item["type"]
                    )

                    st.rerun()

            with col3:
                if st.button(
                    "✍️ Add Review",
                    key=f"watch_review_{index}"
                ):
                    drafts = load_review_drafts()

                    draft_key = f"{item['type']}::{item['title']}".lower()
                    saved_draft = drafts.get(draft_key)

                    # If the watchlist type is Unknown, look for a draft
                    # with the same title under any media type.
                    if not saved_draft and item["type"] == "Unknown":
                        title_suffix = f"::{item['title']}".lower()

                        for key, draft in drafts.items():
                            if key.endswith(title_suffix):
                                saved_draft = draft
                                break

                    st.session_state.review_title = item["title"]

                    if saved_draft:
                        st.session_state.review_type = saved_draft.get("type", "Other")
                    else:
                        st.session_state.review_type = (
                            item["type"]
                            if item["type"] != "Unknown"
                            else "Other"
                        )

                    if saved_draft:
                        st.session_state.review_rating = saved_draft.get("rating", 7)
                        st.session_state.review_thoughts = saved_draft.get("thoughts", "")
                    else:
                        st.session_state.review_rating = 7
                        st.session_state.review_thoughts = ""

                    st.session_state.next_tab = "✍️ Add Review"
                    st.rerun()

            with col4:
                if st.button(
                    "💬 Chat",
                    key=f"watch_chat_{index}"
                ):
                    st.session_state.media_chat_title = item["title"]
                    st.session_state.media_chat_type = (
                        item["type"]
                        if item["type"] != "Unknown"
                        else "Other"
                    )
                    st.session_state.next_tab = "💬 Media Chat"
                    st.rerun()

            st.divider()


# =====================================================
# ADD REVIEW
# =====================================================

with tab4:

    st.header("Add something you've consumed")

    # Media Chat runs later in the script than these widgets, so it hands
    # review drafts back through temporary keys that are applied on rerun.
    if "pending_review_from_chat" in st.session_state:
        pending_review = st.session_state.pop("pending_review_from_chat")
        st.session_state.review_title = pending_review.get("title", "")
        st.session_state.review_type = pending_review.get("type", "Other")
        st.session_state.review_rating = pending_review.get("rating", 7)
        st.session_state.review_thoughts = pending_review.get("thoughts", "")

    with st.expander("🧠 Memory jogger", expanded=False):
        st.caption(
            "Generate things you're likely to have already seen, played, read, "
            "or heard — especially ones you may have a useful opinion about."
        )

        memory_col1, memory_col2 = st.columns([2, 1])

        with memory_col1:
            memory_type = st.selectbox(
                "What should I jog your memory about?",
                ["Any", "TV", "Movie", "Game", "Book", "Music", "Essay", "Other"],
                key="review_memory_type"
            )

        with memory_col2:
            st.write("")
            st.write("")
            generate_memory = st.button(
                "Suggest a few",
                type="primary",
                key="review_memory_generate",
                width="stretch"
            )

        if generate_memory:
            excluded = list(
                st.session_state.get("review_memory_dismissed", [])
            )

            # A fresh batch should not immediately repeat the batch already onscreen.
            for candidate in st.session_state.get(
                "review_memory_suggestions", []
            ):
                if candidate.get("title"):
                    excluded.append(candidate["title"])

            with st.spinner("Jogging your memory..."):
                try:
                    result = suggest_review_candidates(
                        media_type=memory_type,
                        excluded_titles=excluded,
                        count=6
                    )
                    st.session_state.review_memory_suggestions = [
                        item.model_dump()
                        for item in result.suggestions
                    ]
                except Exception as e:
                    st.error(f"Couldn't generate memory joggers: {e}")

        suggestions = st.session_state.get(
            "review_memory_suggestions", []
        )

        if suggestions:
            st.caption(
                "Not recommendations — these are guesses about things you may "
                "already know. Dismiss misses and they won't repeat this session."
            )

            for i, candidate in enumerate(suggestions):
                title = candidate.get("title", "Untitled")
                candidate_type = candidate.get("media_type", "Other")
                reason = candidate.get("reason", "")
                confidence = candidate.get("confidence", "").title()

                st.markdown(f"**{title}** · {candidate_type}")
                if reason:
                    st.write(reason)
                if confidence:
                    st.caption(f"Likelihood guess: {confidence}")

                action_col1, action_col2 = st.columns(2)

                with action_col1:
                    if st.button(
                        "✍️ Review this",
                        key=f"memory_review_{i}_{title}",
                        width="stretch"
                    ):
                        quick_review_dialog(title, candidate_type)

                with action_col2:
                    if st.button(
                        "Haven't consumed it",
                        key=f"memory_skip_{i}_{title}",
                        width="stretch"
                    ):
                        dismissed = set(
                            st.session_state.get(
                                "review_memory_dismissed", []
                            )
                        )
                        dismissed.add(title)
                        st.session_state.review_memory_dismissed = sorted(
                            dismissed
                        )
                        st.session_state.review_memory_suggestions = [
                            item
                            for item in suggestions
                            if item.get("title") != title
                        ]
                        st.rerun()

                st.divider()

        elif "review_memory_suggestions" in st.session_state:
            st.info(
                "No new candidates in that batch. Try another media type "
                "or generate again."
            )

    review_title = st.text_input(
        "Title",
        key="review_title"
    )

    review_type_options = [
        "TV",
        "Movie",
        "Game",
        "Book",
        "Music",
        "Essay",
        "Other"
    ]



    review_type = st.selectbox(
        "Type",
        review_type_options,
        key="review_type"
    )


    rating = st.slider(
        "Rating",
        min_value=1,
        max_value=10,
        key="review_rating"
    )

    thoughts = st.text_area(
        "What did you think?",
        height=180,
        key="review_thoughts"
    )

    if review_title.strip():
        if st.button(
            "💬 Discuss this first",
            key="review_open_chat"
        ):
            st.session_state.media_chat_title = review_title
            st.session_state.media_chat_type = review_type
            st.session_state.next_tab = "💬 Media Chat"
            st.rerun()


    if st.button(
        "💾 Save Draft",
        key="save_review_draft_button"
    ):
        if not review_title.strip():
            st.warning("Enter a title first.")

        else:
            save_review_draft(
                review_title,
                review_type,
                rating,
                thoughts
            )

            st.success("Draft saved.")

    review_web = st.checkbox(
        "Search the web for current information",
        value=False,
        key="review_web_search",
        help="Usually unnecessary: review analysis should prioritize your own impressions."
    )

    if st.button(
        "Save review",
        key="save_review_button",
        type="primary"
    ):

        if not review_title.strip():
            st.warning("Enter a title.")

        elif not thoughts.strip():
            st.warning(
                "Give me at least a little reaction."
            )

        else:

            with st.spinner(
                "Extracting taste signals..."
            ):

                try:
                    analysis = add_review(
                        review_title,
                        review_type,
                        rating,
                        thoughts,
                        web_search=review_web
                    )

                    delete_review_draft(
                        review_title,
                        review_type
                    )

                    st.success(
                        "Review saved and added "
                        "to your retrieval corpus."
                    )

                    for key in [
                        "prefill_review_title",
                        "prefill_review_type",
                        "prefill_rating",
                        "prefill_thoughts"
                    ]:
                        st.session_state.pop(key, None)


                    st.subheader(
                        "What the system learned"
                    )

                    for signal in analysis.taste_signals:
                        st.write("•", signal)

                except Exception as e:
                    st.error(str(e))




# =====================================================
# MEDIA CHAT
# =====================================================

with tab5:

    st.header("Talk about what you're watching, playing, reading, or hearing")
    st.caption(
        "Conversation stays attached to the work. Nothing becomes a taste signal "
        "unless you explicitly approve it."
    )

    media_types = ["TV", "Movie", "Game", "Book", "Music", "Essay", "Other"]

    if "media_chat_title" not in st.session_state:
        st.session_state.media_chat_title = ""
    if "media_chat_type" not in st.session_state:
        st.session_state.media_chat_type = "TV"
    if st.session_state.media_chat_type not in media_types:
        st.session_state.media_chat_type = "Other"

    chat_top1, chat_top2 = st.columns([3, 1])

    with chat_top1:
        chat_title = st.text_input(
            "Title",
            key="media_chat_title",
            placeholder="What are you in the middle of?"
        )

    with chat_top2:
        chat_type = st.selectbox(
            "Type",
            media_types,
            key="media_chat_type"
        )

    chat_context1, chat_context2 = st.columns([2, 1])

    with chat_context1:
        chat_progress = st.text_input(
            "Where are you?",
            key="media_chat_progress",
            placeholder="e.g. S2E5, 8 hours in, chapter 12, finished"
        )

    with chat_context2:
        spoiler_mode = st.selectbox(
            "Spoilers",
            [
                "No spoilers",
                "Only up to my progress",
                "Full spoilers"
            ],
            key="media_chat_spoilers"
        )

    if chat_title.strip():
        messages = load_media_chat(chat_title, chat_type)
        notes = load_media_notes(chat_title, chat_type)

        utility1, utility2, utility3 = st.columns(3)

        with utility1:
            if st.button(
                "✍️ Turn chat into review draft",
                key="chat_make_review",
                width="stretch",
                disabled=not any(
                    item.get("role") == "user"
                    for item in messages
                )
            ):
                with st.spinner("Building a draft from your own remarks..."):
                    try:
                        draft = draft_review_from_chat(
                            chat_title,
                            chat_type,
                            messages,
                            notes
                        )
                        save_review_draft(
                            chat_title,
                            chat_type,
                            draft.suggested_rating or 7,
                            draft.thoughts
                        )
                        st.session_state.pending_review_from_chat = {
                            "title": chat_title,
                            "type": chat_type,
                            "rating": draft.suggested_rating or 7,
                            "thoughts": draft.thoughts
                        }
                        st.session_state.next_tab = "✍️ Add Review"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Couldn't build review draft: {e}")

        with utility2:
            if st.button(
                "📝 Saved notes",
                key="chat_show_notes",
                width="stretch"
            ):
                st.session_state.chat_notes_open = not st.session_state.get(
                    "chat_notes_open", False
                )

        with utility3:
            if st.button(
                "🗑️ Clear this chat",
                key="chat_clear",
                width="stretch",
                disabled=not bool(messages)
            ):
                clear_media_chat(chat_title, chat_type)
                st.session_state.pop("pending_taste_signal", None)
                st.rerun()

        if st.session_state.get("chat_notes_open"):
            with st.expander("Saved notes for this work", expanded=True):
                if notes:
                    for note in notes:
                        source = note.get("source", "note").title()
                        st.markdown(f"**{source}:** {note.get('text', '')}")
                else:
                    st.caption("No saved notes yet.")

        if not messages:
            st.info(
                "Start anywhere: a reaction, a question, something that confused "
                "you, or a comparison to another work."
            )

        for i, message in enumerate(messages):
            role = message.get("role", "assistant")
            content = message.get("content", "")

            with st.chat_message(role):
                st.markdown(content)

                action1, action2 = st.columns(2)

                with action1:
                    note_label = (
                        "📌 Save as reaction"
                        if role == "user"
                        else "📌 Save as reference note"
                    )
                    if st.button(
                        note_label,
                        key=f"chat_note_{i}_{role}",
                        width="stretch"
                    ):
                        save_media_note(
                            chat_title,
                            chat_type,
                            content,
                            source=role
                        )
                        st.toast("Saved with this work.")

                with action2:
                    if role == "user":
                        if st.button(
                            "🧠 Extract taste signal",
                            key=f"chat_signal_{i}",
                            width="stretch"
                        ):
                            with st.spinner("Looking for a durable taste signal..."):
                                try:
                                    candidate = extract_taste_signal_from_excerpt(
                                        chat_title,
                                        chat_type,
                                        content
                                    )
                                    st.session_state.pending_taste_signal = {
                                        "title": chat_title,
                                        "type": chat_type,
                                        "excerpt": content,
                                        "signal": candidate.signal,
                                        "confidence": candidate.confidence,
                                        "rationale": candidate.rationale
                                    }
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Couldn't extract signal: {e}")

        pending = st.session_state.get("pending_taste_signal")
        if pending and pending.get("title") == chat_title:
            with st.container(border=True):
                st.markdown("#### Proposed taste signal")
                st.write(pending.get("signal", ""))
                st.caption(
                    f"Confidence: {pending.get('confidence', '').title()} · "
                    f"{pending.get('rationale', '')}"
                )

                approve_col, dismiss_col = st.columns(2)

                with approve_col:
                    if st.button(
                        "✓ Add to taste profile",
                        key="approve_taste_signal",
                        type="primary",
                        width="stretch"
                    ):
                        save_manual_taste_signal(
                            pending["title"],
                            pending["type"],
                            pending["signal"],
                            pending.get("excerpt", "")
                        )
                        st.session_state.pop("pending_taste_signal", None)
                        st.toast("Added to your live taste profile.")
                        st.rerun()

                with dismiss_col:
                    if st.button(
                        "Dismiss",
                        key="dismiss_taste_signal",
                        width="stretch"
                    ):
                        st.session_state.pop("pending_taste_signal", None)
                        st.rerun()

        user_prompt = st.chat_input(
            f"Talk about {chat_title}...",
            key="media_chat_input"
        )

        if user_prompt:
            messages.append({
                "role": "user",
                "content": user_prompt
            })
            save_media_chat(chat_title, chat_type, messages)

            with st.spinner("Thinking..."):
                try:
                    reply = chat_about_media(
                        chat_title,
                        chat_type,
                        messages,
                        progress=chat_progress,
                        spoiler_mode=spoiler_mode
                    )
                    messages.append({
                        "role": "assistant",
                        "content": reply
                    })
                    save_media_chat(chat_title, chat_type, messages)
                    st.rerun()
                except Exception as e:
                    st.error(f"Chat failed: {e}")

    else:
        st.info(
            "Enter a title, or open Media Chat from a Watchlist item or review."
        )


# =====================================================
# PROFILE
# =====================================================

with tab6:

    st.header("Current cross-media taste profile")

    try:
        profile = load_profile()
        st.markdown(profile)

        manual_signals = load_manual_taste_signals()
        with st.expander(
            f"User-approved signals ({len(manual_signals)})",
            expanded=False
        ):
            if manual_signals:
                st.caption(
                    "These are explicitly approved additions. They are appended "
                    "to the live profile context without rewriting the base profile."
                )
                for i, signal in enumerate(manual_signals):
                    sig_col, remove_col = st.columns([5, 1])
                    with sig_col:
                        st.write(signal.get("signal", ""))
                        if signal.get("title"):
                            st.caption(
                                f"From {signal.get('title')} · "
                                f"{signal.get('type', 'Other')}"
                            )
                    with remove_col:
                        if st.button(
                            "Remove",
                            key=f"remove_manual_signal_{i}"
                        ):
                            remove_manual_taste_signal(i)
                            st.rerun()
            else:
                st.caption(
                    "No manually approved signals yet. Extract one from Media Chat "
                    "when a conversation surfaces something durable."
                )

    except Exception as e:
        st.error(
            f"Could not load taste profile: {e}"
        )