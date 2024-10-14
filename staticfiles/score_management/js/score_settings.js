document.addEventListener('DOMContentLoaded', function () {
    const editModal = document.getElementById('editModal');
    const deleteModal = document.getElementById('deleteModal');
    const deleteForm = document.getElementById('deleteForm');  // 削除フォームを取得

    // 編集ボタンをクリックしたときの処理
    document.querySelectorAll('.edit-button').forEach(button => {
        button.addEventListener('click', function () {
            const scoreId = this.dataset.scoreId;
            const actionType = this.dataset.actionType;
            const trigger = this.dataset.trigger;
            const score = this.dataset.score;
            const memo = this.dataset.memo;
            const tagName = this.dataset.tagName;
            const tagColor = this.dataset.tagColor;

            document.getElementById('edit_action_type').value = actionType;
            document.getElementById('edit_trigger').value = trigger;
            document.getElementById('edit_score').value = score;
            document.getElementById('edit_memo').value = memo;
            document.getElementById('edit_tag_name').value = tagName;
            document.getElementById('edit_tag_color').value = tagColor;

            document.getElementById('editForm').action = `/score/edit/${scoreId}/`;

            editModal.classList.remove('hidden');
        });
    });

    // 削除ボタンをクリックしたときの処理
    document.querySelectorAll('.delete-button').forEach(button => {
    button.addEventListener('click', function () {
        const scoreId = this.dataset.scoreId;
        deleteForm.action = `/score/delete/${scoreId}/`;
        deleteModal.classList.remove('hidden');
    });
});

    // 編集モーダルのキャンセルボタンをクリックしたときの処理
    document.getElementById('cancelEdit').addEventListener('click', function () {
        editModal.classList.add('hidden');
    });

    // 削除モーダルのキャンセルボタンをクリックしたときの処理
    document.getElementById('cancelDelete').addEventListener('click', function () {
        deleteModal.classList.add('hidden');
    });

    // 確認用の削除ボタンをクリックしたときの処理
        deleteForm.addEventListener('submit', function (event) {
        event.preventDefault();  // デフォルトのフォーム送信を防止

        const action = deleteForm.action;

        fetch(action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                window.location.href = '/score/score_settings/';  // 成功したらスコア設定ページにリダイレクト
            } else {
                alert('削除に失敗しました');
            }
        })
        .catch(error => {
            console.error('エラー:', error);
            alert('エラーが発生しました。もう一度お試しください。');
        });
    });
});
