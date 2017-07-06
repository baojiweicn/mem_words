function getURLParameter(name) {
    return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search)||[,""])[1].replace(/\+/g, '%20'))||null;
};

window.onload = function(){
  load_wordlists();
};

function load_wordlists(){
  res = get_wordlists();
  if(res.status == 200){
      wordlists = res.responseJSON;
      adapt_wordlist(wordlists);
    document.getElementById("details").style.visibility = "";
  } 
  else{
      document.getElementById("query").innerHTML = "请登录";
  }   
}

function get_wordlists(){
  var url = "/words/wordlists/";
  var res = $.ajax({url:url,async:false});
  return res;
};

function adapt_wordlist(wordlists){
  radios = "<form>"
  for(var i=0;i<wordlists.length;i++){
    wordlist = wordlists[i];
    wordlist_name = wordlist["name"];
    wordlist_id = wordlist["id"]
    radio = "<input type=\"radio\" name=\"wordlists\" value=\""+wordlist_id+"\" checked><span> &nbsp"+wordlist_name+"</span><br>";
    radios = radios + radio;
  }
  radios = radios + "</form>";
  radio_list = document.getElementById("details").children[0];
  radio_list.innerHTML = radios;
};

function add_wordlist(wordlist_name){
  var url = "/words/wordlists";
  var data = {"name":wordlist_name};
  var res = $.ajax({
    url:url,
    data: JSON.stringify(data),
    type:'post',
    dataType:'json',
    success: function(data){
      load_wordlists();
    }
  });
};

function delete_wordlist(wordlist_name){
    var url = "/words/wordlists";
  var data = {"name":wordlist_name};
  var res = $.ajax({
    url:url,
    data: JSON.stringify(data),
    type:'delete',
    dataType:'json',
    success: function(data){
      load_wordlists();
    }
  });
};

function user_login(username){
  var url = "/words/users";
  var data = {"username":username};
  var res = $.ajax({type: 'POST',url: url,data: JSON.stringify(data),dataType: "json"});
  return res;
};

function get_wordlist_words(wordlist_id){
  var url = "/words/wordlists/" + wordlist_id + "/review";
  var res = $.ajax({url:url,async:false});
  return res;
};

function set_wordlist_words(wordlist_id){
  var url = "/words/wordlists/" + wordlist_id + "/review";
  var put_data = [];
  var words_key = Object.keys(words_result);
  for(var i=0;i<words_key.length;i++){
    put_data.push({
      "word": words_key[i],
      "state": words_result[words_key[i]]
    })
  }
  return

};

function set_query(query){
	document.getElementById("query").textContent = query;
  document.getElementById("pronounce").src = '/words/audios/' + query;
  var res = load_explain(query);
  var res_basic = res.responseJSON.basic;
  var res_web = res.responseJSON.web;
  set_query_phonetic(res_basic);
  set_query_explain(res_basic);
  set_query_examples(res_web);
};

function load_explain(query){
	var url = "/words/translates/" + query;
	var res = $.ajax({url:url,async:false});
  return res;
};

function set_query_phonetic(res_basic){
	var phonetics_text = '[uk]' + res_basic['uk-phonetic'] + ' [us]' + res_basic['us-phonetic'];
  document.getElementById("phonetic").textContent = phonetics_text;
};

function set_query_explain(res_basic){
  var explain_text = '';
  var explains = res_basic.explains;
  for (var i=0;i<explains.length;i++){
    explain_text += explains[i] + '<br>';
  };
  document.getElementById("explain").innerHTML = explain_text.toString();
};

function set_query_examples(res_web){
  var examples_text = '';
  for (var i=0;i<res_web.length;i++){
    examples_text += res_web[i]['key'] + ': ' + res_web[i]['value'].join("；") + '<br>';
  };
  document.getElementById("examples").innerHTML = examples_text.toString();
};

function next_word(){
  document.getElementById("details").style.visibility = 'hidden';
  words_result[words[words_index]] = word_state;
  if(words_index<words.length && words.length>0){
    if(word_state == 'remember'){
      words.splice(words_index,1);
      words_index -=1;
      //check_empty();
    }
    else if (words[words_index] in words_tmp){
      if (words_tmp[words[words_index]] ==3 ){
        words.splice(words_index,1);
        words_index -=1;
        //check_empty();
      }
      else{
        words_tmp[words[words_index]] += 1;
      }
    }
    else {
      words_tmp[words[words_index]] = 1;
    }
    words_index +=1;
    if(words_index == words.length){
      words_index=0;
    }  
  }
  else if(words_index>=words.length){
    words_index=0;
  }
  check_empty();
  update_word(words_index);
};


document.getElementById("delete_wordlist").onclick = function(){
  wordlist_name = $(":radio:checked + span").text().replace(/^\s+|\s+$/g,"")
  delete_wordlist(wordlist_name);
};


document.getElementById("select_wordlist").onclick = function(){
  wordlist_id = $('input:radio:checked').val();
  window.location.href='/html/WordList.html?wordlist_id='+wordlist_id;
};

document.getElementById("add_wordlist").onclick = function(){
  document.getElementById("input_area").style.visibility = "";
};

document.getElementById("verifty").onclick = function(){
  wordlist_name = $("#wordlist_input").val().replace(/^\s+|\s+$/g,"");
  if(wordlist_name !=""){
    add_wordlist(wordlist_name);
  }
};

document.getElementById("cancle").onclick = function(){
  document.getElementById("input_area").style.visibility = "hidden";
};


